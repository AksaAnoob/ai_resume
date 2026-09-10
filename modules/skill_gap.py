from typing import List, Dict, Any

def analyze_skill_gap(resume_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
    """
    Compares skills extracted from resume against required skills from job description.
    
    Args:
        resume_skills: List of skills found in resume.
        job_skills: List of skills required by job description.
        
    Returns:
        Dictionary containing:
        - matching_skills (List[str])
        - missing_skills (List[str])
        - extra_skills (List[str])
        - skill_match_percentage (float)
    """
    set_resume = set(resume_skills)
    set_job = set(job_skills)

    matching_skills = sorted(list(set_resume.intersection(set_job)))
    missing_skills = sorted(list(set_job.difference(set_resume)))
    extra_skills = sorted(list(set_resume.difference(set_job)))

    if not set_job:
        # If no explicit skills were extracted from JD, but resume has skills
        match_pct = 100.0 if set_resume else 0.0
    else:
        match_pct = (len(matching_skills) / len(set_job)) * 100.0

    return {
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills,
        "skill_match_percentage": round(match_pct, 2)
    }
