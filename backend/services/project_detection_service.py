import re
from typing import List, Dict, Any, Optional

class ProjectDetectionService:
    def detect_project_number_in_email(self, email_text: str) -> List[str]:
        """
        Detect project numbers in email text (YY-NNNN format).
        Handles variations: "25-0308", "25 0308", "250308", "Project 25-0308".
        """
        if not email_text:
            return []

        # Pattern explanation:
        # \b(2[0-9]) : YY starting with 2 (assuming 20s for now, e.g., 20-29).
        #            The Altimeter service used 2[4-9], but I'll stick to 2[0-9] to cover 2020-2029.
        # [- ]?      : Optional separator (dash or space).
        # (\d{4})\b  : 4 digits.
        pattern = r"\b(2[0-9])[- ]?(\d{4})\b"

        matches = re.findall(pattern, email_text)
        detected = []
        for match in matches:
            # match is a tuple (YY, NNNN)
            normalized = f"{match[0]}-{match[1]}"
            if normalized not in detected:
                detected.append(normalized)

        return detected

    def match_detected_projects_to_altimeter(self, project_numbers: List[str], altimeter_service) -> List[Dict[str, Any]]:
        """
        Match detected project numbers to Altimeter projects.
        """
        matches = []
        # Remove duplicates
        unique_numbers = list(set(project_numbers))

        for number in unique_numbers:
            # Verify with Altimeter service
            project_details = altimeter_service.get_project_details(number)
            if project_details:
                matches.append({
                    "number": number,
                    "name": project_details.get("name"),
                    "status": project_details.get("status"),
                    "confidence": 1.0 # High confidence if matched in DB
                })
        return matches

project_detection_service = ProjectDetectionService()
