"""Fix resume file paths in database."""
import asyncio
from pathlib import Path
from database import async_session_maker
from models.resume import Resume
from sqlalchemy import select


async def fix_paths():
    async with async_session_maker() as session:
        result = await session.execute(select(Resume))
        resumes = result.scalars().all()

        upload_dir = Path("data/uploads")

        for resume in resumes:
            # Try to find file by CV number from filename
            # Filename is like "CV_1.docx", so file should be "1.docx"
            import re
            match = re.search(r'CV_(\d+)', resume.filename)
            if match:
                cv_num = match.group(1)
                potential_file = upload_dir / f"{cv_num}.docx"
                if potential_file.exists():
                    old_path = resume.file_path
                    resume.file_path = str(potential_file)
                    print(f"Updated {resume.filename}: {old_path} -> {resume.file_path}")

        await session.commit()
        print(f"Processed {len(resumes)} resumes")


if __name__ == "__main__":
    asyncio.run(fix_paths())
