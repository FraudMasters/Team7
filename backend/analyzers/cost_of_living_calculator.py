"""
Cost of Living Calculator for Geographic Salary Adjustments

This module provides cost-of-living calculations for geographic salary adjustments.
It considers multiple factors including:
- Overall cost-of-living index by location
- Category-specific indices (housing, transportation, groceries, utilities, healthcare)
- Location-based salary normalization
- Multi-location salary comparisons
- Currency considerations
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models import CostOfLivingIndex
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)


class CostOfLivingCalculator:
    """
    Calculator for geographic cost-of-living adjustments.

    Provides methods to adjust salaries based on geographic location,
    compare costs across locations, and normalize compensation data.
    """

    def __init__(self):
        """Initialize the cost-of-living calculator."""
        self.version = "1.0.0"

    async def get_location_index(
        self,
        db: AsyncSession,
        location: str,
        country: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cost-of-living index for a specific location.

        Args:
            db: Database session
            location: Geographic location (city, state, or country)
            country: Optional country code for filtering

        Returns:
            Cost-of-living data or None if not found
        """
        try:
            # Build query
            conditions = []

            # Try exact match first
            conditions.append(CostOfLivingIndex.location == location)

            # Try partial match
            conditions.append(CostOfLivingIndex.location.ilike(f"%{location}%"))

            # Add country filter if provided
            if country:
                conditions.append(CostOfLivingIndex.country == country)

            # Query with OR conditions for flexible matching
            query = select(CostOfLivingIndex).where(
                or_(*conditions[:2])  # Use first two conditions (exact and partial match)
            )

            if country:
                query = query.where(CostOfLivingIndex.country == country)

            # Order by data_source (prefer 'api' over 'internal') and recency
            query = query.order_by(
                CostOfLivingIndex.data_source.desc(),
                CostOfLivingIndex.updated_at.desc()
            )

            result = await db.execute(query)
            index_record = result.scalar_one_or_none()

            if not index_record:
                logger.warning(f"No cost-of-living index found for location={location}")
                return None

            return {
                "id": str(index_record.id),
                "location": index_record.location,
                "country": index_record.country,
                "region": index_record.region,
                "cost_of_living_index": float(index_record.cost_of_living_index),
                "housing_index": float(index_record.housing_index) if index_record.housing_index else None,
                "transportation_index": float(index_record.transportation_index) if index_record.transportation_index else None,
                "groceries_index": float(index_record.groceries_index) if index_record.groceries_index else None,
                "utilities_index": float(index_record.utilities_index) if index_record.utilities_index else None,
                "healthcare_index": float(index_record.healthcare_index) if index_record.healthcare_index else None,
                "currency": index_record.currency,
                "data_source": index_record.data_source,
                "effective_date": index_record.effective_date,
                "metadata": index_record.metadata or {},
            }

        except Exception as e:
            logger.error(f"Error fetching location index: {e}", exc_info=True)
            return None

    async def get_adjustment_factor(
        self,
        db: AsyncSession,
        location: str,
        baseline_location: str = "National Average",
        category: Optional[str] = None,
    ) -> float:
        """
        Calculate cost-of-living adjustment factor for a location.

        Args:
            db: Database session
            location: Target location
            baseline_location: Baseline location for comparison (default: National Average)
            category: Optional category (housing, transportation, etc.) for specific adjustment

        Returns:
            Adjustment factor (e.g., 1.2 for 20% higher cost, 0.8 for 20% lower)
        """
        try:
            # Get target location index
            target_data = await self.get_location_index(db, location)

            if not target_data:
                return 1.0  # No adjustment if data not found

            target_index = target_data["cost_of_living_index"]

            # If category specified, use category-specific index
            if category and target_data.get(f"{category}_index"):
                category_key = f"{category}_index"
                target_index = target_data[category_key]

            # Get baseline location index (if not National Average)
            baseline_index = 100.0  # Default baseline
            if baseline_location != "National Average":
                baseline_data = await self.get_location_index(db, baseline_location)
                if baseline_data:
                    baseline_index = baseline_data["cost_of_living_index"]
                    if category and baseline_data.get(f"{category}_index"):
                        baseline_index = baseline_data[f"{category}_index"]

            # Calculate adjustment factor
            adjustment_factor = target_index / baseline_index

            # Clamp to reasonable range (0.5x to 2.0x)
            return max(0.5, min(adjustment_factor, 2.0))

        except Exception as e:
            logger.error(f"Error calculating adjustment factor: {e}", exc_info=True)
            return 1.0

    async def adjust_salary(
        self,
        db: AsyncSession,
        salary: float,
        from_location: str,
        to_location: str,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Adjust salary from one location to another based on cost-of-living.

        Args:
            db: Database session
            salary: Original salary amount
            from_location: Source location
            to_location: Target location
            category: Optional category for specific adjustment

        Returns:
            Adjusted salary with breakdown
        """
        start_time = datetime.now()

        try:
            # Get adjustment factor (to_location / from_location)
            from_adjustment = await self.get_adjustment_factor(
                db, from_location, baseline_location="National Average", category=category
            )
            to_adjustment = await self.get_adjustment_factor(
                db, to_location, baseline_location="National Average", category=category
            )

            # Calculate relative adjustment
            relative_adjustment = to_adjustment / from_adjustment if from_adjustment > 0 else 1.0

            # Calculate adjusted salary
            adjusted_salary = salary * relative_adjustment

            # Get location data for context
            from_data = await self.get_location_index(db, from_location)
            to_data = await self.get_location_index(db, to_location)

            duration = (datetime.now() - start_time).total_seconds()

            # Record metrics
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="cost_of_living_calculator",
                    operation="adjust_salary",
                    duration=duration,
                    prediction_type="salary_adjustment",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            return {
                "original_salary": salary,
                "adjusted_salary": round(adjusted_salary, 2),
                "from_location": from_location,
                "to_location": to_location,
                "adjustment_factor": round(relative_adjustment, 4),
                "percentage_change": round((relative_adjustment - 1.0) * 100, 2),
                "category": category or "overall",
                "from_location_index": from_data["cost_of_living_index"] if from_data else None,
                "to_location_index": to_data["cost_of_living_index"] if to_data else None,
                "currency": to_data["currency"] if to_data else "USD",
            }

        except Exception as e:
            logger.error(f"Error adjusting salary: {e}", exc_info=True)
            raise

    async def compare_locations(
        self,
        db: AsyncSession,
        locations: List[str],
    ) -> Dict[str, Any]:
        """
        Compare cost-of-living across multiple locations.

        Args:
            db: Database session
            locations: List of location names to compare

        Returns:
            Comparison data with rankings and breakdowns
        """
        try:
            location_data = []

            for location in locations:
                data = await self.get_location_index(db, location)
                if data:
                    location_data.append({
                        "location": data["location"],
                        "country": data.get("country"),
                        "overall_index": data["cost_of_living_index"],
                        "housing": data.get("housing_index"),
                        "transportation": data.get("transportation_index"),
                        "groceries": data.get("groceries_index"),
                        "utilities": data.get("utilities_index"),
                        "healthcare": data.get("healthcare_index"),
                        "currency": data["currency"],
                    })

            if not location_data:
                return {
                    "locations": [],
                    "rankings": [],
                    "cheapest": None,
                    "most_expensive": None,
                }

            # Sort by overall index
            location_data.sort(key=lambda x: x["overall_index"])

            # Calculate rankings
            rankings = []
            for i, loc in enumerate(location_data):
                rankings.append({
                    "rank": i + 1,
                    "location": loc["location"],
                    "overall_index": loc["overall_index"],
                    "percent_above_baseline": round((loc["overall_index"] - 100.0), 2),
                })

            return {
                "locations": location_data,
                "rankings": rankings,
                "cheapest": {
                    "location": location_data[0]["location"],
                    "index": location_data[0]["overall_index"],
                } if location_data else None,
                "most_expensive": {
                    "location": location_data[-1]["location"],
                    "index": location_data[-1]["overall_index"],
                } if location_data else None,
                "count": len(location_data),
            }

        except Exception as e:
            logger.error(f"Error comparing locations: {e}", exc_info=True)
            raise

    async def normalize_salary_to_baseline(
        self,
        db: AsyncSession,
        salary: float,
        location: str,
        baseline_location: str = "National Average",
    ) -> Dict[str, Any]:
        """
        Normalize salary from a specific location to baseline location.

        This is useful for comparing salaries across different locations
        by converting them to a common baseline.

        Args:
            db: Database session
            salary: Salary in the original location
            location: Original location
            baseline_location: Target baseline location

        Returns:
            Normalized salary with breakdown
        """
        try:
            # Get adjustment factor relative to baseline
            adjustment_factor = await self.get_adjustment_factor(
                db, location, baseline_location=baseline_location
            )

            # Normalize salary (divide by adjustment factor)
            normalized_salary = salary / adjustment_factor if adjustment_factor > 0 else salary

            # Get location data
            location_data = await self.get_location_index(db, location)

            return {
                "original_salary": salary,
                "normalized_salary": round(normalized_salary, 2),
                "original_location": location,
                "baseline_location": baseline_location,
                "adjustment_factor": round(adjustment_factor, 4),
                "location_index": location_data["cost_of_living_index"] if location_data else None,
                "currency": location_data["currency"] if location_data else "USD",
            }

        except Exception as e:
            logger.error(f"Error normalizing salary: {e}", exc_info=True)
            raise

    async def compare_salary_purchasing_power(
        self,
        db: AsyncSession,
        salary: float,
        location: str,
        comparison_locations: List[str],
    ) -> Dict[str, Any]:
        """
        Compare purchasing power of a salary across multiple locations.

        Shows what the same salary would feel like in different locations.

        Args:
            db: Database session
            salary: Original salary amount
            location: Original location
            comparison_locations: List of locations to compare against

        Returns:
            Purchasing power comparison across locations
        """
        try:
            # Get original location data
            original_data = await self.get_location_index(db, location)
            original_index = original_data["cost_of_living_index"] if original_data else 100.0

            comparisons = []

            for comp_location in comparison_locations:
                comp_data = await self.get_location_index(db, comp_location)

                if comp_data:
                    comp_index = comp_data["cost_of_living_index"]

                    # Calculate equivalent salary
                    equivalent_salary = salary * (comp_index / original_index)

                    # Calculate purchasing power percentage
                    purchasing_power = (original_index / comp_index) * 100

                    comparisons.append({
                        "location": comp_location,
                        "equivalent_salary": round(equivalent_salary, 2),
                        "purchasing_power_percentage": round(purchasing_power, 2),
                        "cost_of_living_index": comp_index,
                        "more_expensive": comp_index > original_index,
                        "difference_percent": round(((comp_index - original_index) / original_index) * 100, 2),
                    })

            # Sort by equivalent salary (descending)
            comparisons.sort(key=lambda x: x["equivalent_salary"], reverse=True)

            return {
                "original_salary": salary,
                "original_location": location,
                "original_index": original_index,
                "comparisons": comparisons,
                "count": len(comparisons),
            }

        except Exception as e:
            logger.error(f"Error comparing purchasing power: {e}", exc_info=True)
            raise

    async def get_category_breakdown(
        self,
        db: AsyncSession,
        location: str,
    ) -> Dict[str, Any]:
        """
        Get detailed category breakdown for a location.

        Provides cost-of-living breakdown by category (housing, transportation, etc.)

        Args:
            db: Database session
            location: Location name

        Returns:
            Category breakdown with percentages
        """
        try:
            data = await self.get_location_index(db, location)

            if not data:
                return {
                    "location": location,
                    "available": False,
                    "categories": {},
                }

            categories = {
                "housing": data.get("housing_index"),
                "transportation": data.get("transportation_index"),
                "groceries": data.get("groceries_index"),
                "utilities": data.get("utilities_index"),
                "healthcare": data.get("healthcare_index"),
            }

            # Calculate percentage relative to national average (100)
            breakdown = {}
            for category, index in categories.items():
                if index is not None:
                    breakdown[category] = {
                        "index": round(index, 2),
                        "percent_of_baseline": round(index, 2),
                        "above_baseline": index > 100,
                    }

            return {
                "location": location,
                "available": True,
                "overall_index": data["cost_of_living_index"],
                "categories": breakdown,
                "currency": data["currency"],
            }

        except Exception as e:
            logger.error(f"Error getting category breakdown: {e}", exc_info=True)
            return {
                "location": location,
                "available": False,
                "categories": {},
            }


# Global service instance
_cost_of_living_calculator: Optional[CostOfLivingCalculator] = None


def get_cost_of_living_calculator() -> CostOfLivingCalculator:
    """Get or create global cost-of-living calculator instance."""
    global _cost_of_living_calculator
    if _cost_of_living_calculator is None:
        _cost_of_living_calculator = CostOfLivingCalculator()
    return _cost_of_living_calculator
