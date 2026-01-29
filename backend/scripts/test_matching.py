"""
Test matching against ground truth annotations.
"""
import sys
import asyncio
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from sqlalchemy import select
from database import async_session_maker
from models.job_vacancy import JobVacancy

# Ground truth rankings
ANNOTATOR_1 = [
    [2,1,4,3,5],[1,2,3,4,5],[1,2,3,4,5],[3,1,2,4,5],[1,5,4,2,3],
    [3,2,1,4,5],[3,2,1,5,4],[2,4,3,1,5],[1,5,2,1,4],[3,2,1,4,5],
    [1,2,3,4,5],[1,2,3,4,5],[1,3,2,4,5],[1,2,3,4,5],[3,1,2,4,5],
    [3,1,2,4,5],[3,1,2,4,5],[1,2,5,3,4],[3,2,1,4,5],[3,2,1,4,5],
    [2,3,1,4,5],[1,2,3,5,4],[2,1,3,5,4],[1,2,3,5,4],[1,2,3,4,5],
    [2,1,3,4,5],[2,3,4,5,1],[2,4,3,2,5],[5,1,2,4,3],[2,1,4,3,5],
]

ANNOTATOR_2 = [
    [4,3,1,5,2],[2,4,3,1,5],[5,4,2,3,1],[1,3,2,4,5],[5,1,2,4,3],
    [1,3,2,4,5],[4,2,3,1,5],[2,4,3,1,5],[3,4,2,1,5],[4,1,2,5,3],
    [2,4,3,5,1],[4,3,2,1,5],[4,2,3,1,5],[3,4,2,1,5],[2,4,3,1,5],
    [3,2,4,1,5],[4,2,3,1,5],[4,2,5,3,1],[4,2,3,1,5],[1,5,2,4,3],
    [1,3,4,5,2],[4,1,3,2,5],[1,3,4,2,5],[1,4,3,5,2],[1,4,2,5,3],
    [1,5,2,4,3],[4,3,1,2,5],[1,4,2,3,5],[5,1,2,4,3],[1,2,3,4,5],
]

# Map vacancy IDs (1-5) to external IDs
VACANCY_ID_MAP = {
    1: "e3f78c8c36195e4438286bb9395085a0",
    2: "708584f2d49cb195c9fc9d7bee36e699",
    3: "72fafc405b891220ce78df7fd4e72a80",
    4: "5eb96f825590e690d76930c52b9100de",
    5: "296f9b55a3a3eed93ad08924274f2eba",
}

# Reverse map: external_id to vacancy_id (1-5)
EXTERNAL_TO_VACANCY_ID = {v: k for k, v in VACANCY_ID_MAP.items()}


async def get_vacancies():
    """Get all vacancies from database."""
    async with async_session_maker() as session:
        result = await session.execute(select(JobVacancy))
        return result.scalars().all()


async def match_resume(resume_id: str):
    """Match resume against all vacancies via API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/vacancies/match-all?resume_id={resume_id}",
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()


def dcg(relevance_scores):
    """Calculate DCG (Discounted Cumulative Gain)."""
    dcg_value = 0.0
    for i, score in enumerate(relevance_scores):
        # log2(i+2) because i starts at 0
        dcg_value += score / __import__('math').log2(i + 2)
    return dcg_value


def ndcg(predicted_ranking, true_ranking):
    """Calculate NDCG (Normalized DCG)."""
    # Create relevance scores based on true ranking (position 1 = rel 5, position 5 = rel 1)
    relevance = {}
    for i, vac_id in enumerate(true_ranking):
        relevance[vac_id] = 5 - i  # 5 for rank 1, 1 for rank 5
    
    # DCG of predicted ranking
    predicted_scores = [relevance.get(vac_id, 0) for vac_id in predicted_ranking]
    dcg_value = dcg(predicted_scores)
    
    # Ideal DCG (perfect ranking)
    ideal_scores = sorted(relevance.values(), reverse=True)
    idcg_value = dcg(ideal_scores)
    
    if idcg_value == 0:
        return 0.0
    return dcg_value / idcg_value


def precision_at_k(predicted_ranking, true_ranking, k):
    """Calculate Precision@K."""
    # Top-k from predicted
    top_k_predicted = set(predicted_ranking[:k])
    # Top-k from true (best matches)
    top_k_true = set(true_ranking[:k])
    
    if not top_k_predicted:
        return 0.0
    
    return len(top_k_predicted & top_k_true) / k


def average_precision(predicted_ranking, true_ranking):
    """Calculate Average Precision."""
    hits = 0
    sum_precision = 0.0
    
    for i, vac_id in enumerate(predicted_ranking):
        if vac_id in true_ranking:
            hits += 1
            sum_precision += hits / (i + 1)
    
    if hits == 0:
        return 0.0
    
    return sum_precision / len(true_ranking)


async def run_evaluation():
    """Run matching evaluation against ground truth."""
    vacancies = await get_vacancies()
    print(f"Found {len(vacancies)} vacancies in database\n")
    
    # Build external_id to index map
    ext_to_idx = {str(v.id): EXTERNAL_TO_VACANCY_ID.get(v.external_id) for v in vacancies}
    
    results = []
    ndcg_scores_a1 = []
    ndcg_scores_a2 = []
    precision_1_a1 = []
    precision_1_a2 = []
    precision_3_a1 = []
    precision_3_a2 = []
    
    print("Testing matching for first 30 CVs against ground truth...\n")
    
    for cv_num in range(1, 31):
        resume_id = str(cv_num)
        
        try:
            # Get match results
            match_result = await match_resume(resume_id)
            
            # Extract predicted ranking (vacancy IDs 1-5)
            predicted = []
            for match in match_result.get('matches', []):
                vac_ext_id = match.get('vacancy_id')
                vac_id = ext_to_idx.get(vac_ext_id)
                if vac_id:
                    predicted.append(vac_id)
            
            # Ground truth rankings
            true_a1 = ANNOTATOR_1[cv_num - 1]
            true_a2 = ANNOTATOR_2[cv_num - 1]
            
            # Calculate metrics
            ndcg_a1 = ndcg(predicted, true_a1)
            ndcg_a2 = ndcg(predicted, true_a2)
            
            p1_a1 = precision_at_k(predicted, true_a1, 1)
            p1_a2 = precision_at_k(predicted, true_a2, 1)
            
            p3_a1 = precision_at_k(predicted, true_a1, 3)
            p3_a2 = precision_at_k(predicted, true_a2, 3)
            
            ndcg_scores_a1.append(ndcg_a1)
            ndcg_scores_a2.append(ndcg_a2)
            precision_1_a1.append(p1_a1)
            precision_1_a2.append(p1_a2)
            precision_3_a1.append(p3_a1)
            precision_3_a2.append(p3_a2)
            
            results.append({
                'cv': cv_num,
                'predicted': predicted,
                'true_a1': true_a1,
                'true_a2': true_a2,
                'ndcg_a1': ndcg_a1,
                'ndcg_a2': ndcg_a2,
                'p1_a1': p1_a1,
                'p1_a2': p1_a2,
            })
            
            # Print individual results
            best_match = predicted[0] if predicted else None
            best_a1 = true_a1[0]
            best_a2 = true_a2[0]
            match_icon = "✓" if best_match == best_a1 or best_match == best_a2 else "✗"
            
            print(f"CV {cv_num:2d}: Pred=[{predicted[0] if predicted else '?'}] A1=[{best_a1}] A2=[{best_a2}] {match_icon}  NDCG: A1={ndcg_a1:.2f} A2={ndcg_a2:.2f}")
            
        except Exception as e:
            print(f"CV {cv_num}: ERROR - {e}")
    
    # Calculate averages
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80)
    
    avg_ndcg_a1 = sum(ndcg_scores_a1) / len(ndcg_scores_a1)
    avg_ndcg_a2 = sum(ndcg_scores_a2) / len(ndcg_scores_a2)
    avg_p1_a1 = sum(precision_1_a1) / len(precision_1_a1)
    avg_p1_a2 = sum(precision_1_a2) / len(precision_1_a2)
    avg_p3_a1 = sum(precision_3_a1) / len(precision_3_a1)
    avg_p3_a2 = sum(precision_3_a2) / len(precision_3_a2)
    
    print(f"\nAnnotator 1:")
    print(f"  NDCG:           {avg_ndcg_a1:.4f}")
    print(f"  Precision@1:    {avg_p1_a1:.4f}")
    print(f"  Precision@3:    {avg_p3_a1:.4f}")
    
    print(f"\nAnnotator 2:")
    print(f"  NDCG:           {avg_ndcg_a2:.4f}")
    print(f"  Precision@1:    {avg_p1_a2:.4f}")
    print(f"  Precision@3:    {avg_p3_a2:.4f}")
    
    print(f"\nAverage (both annotators):")
    print(f"  NDCG:           {(avg_ndcg_a1 + avg_ndcg_a2)/2:.4f}")
    print(f"  Precision@1:    {(avg_p1_a1 + avg_p1_a2)/2:.4f}")
    print(f"  Precision@3:    {(avg_p3_a1 + avg_p3_a2)/2:.4f}")
    
    # Count perfect matches
    perfect_a1 = sum(1 for r in results if r['predicted'] and r['predicted'][0] == r['true_a1'][0])
    perfect_a2 = sum(1 for r in results if r['predicted'] and r['predicted'][0] == r['true_a2'][0])
    perfect_either = sum(1 for r in results if r['predicted'] and (r['predicted'][0] == r['true_a1'][0] or r['predicted'][0] == r['true_a2'][0]))
    
    print(f"\nTop-1 Accuracy:")
    print(f"  Annotator 1:    {perfect_a1}/30 ({perfect_a1/30*100:.1f}%)")
    print(f"  Annotator 2:    {perfect_a2}/30 ({perfect_a2/30*100:.1f}%)")
    print(f"  Either match:   {perfect_either}/30 ({perfect_either/30*100:.1f}%)")
    
    print("="*80)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
