"""Parser for DEVELOPMENT_PLAN.md files."""

import re
from pathlib import Path
from typing import List, Optional

import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension

from orchestrator.core.models import Phase, Plan, Stage, Task, TaskType, Complexity


class StructureExtractor(Treeprocessor):
    """Custom tree processor to extract document structure."""

    def run(self, root):
        """Extract structure from markdown tree."""
        self.structure = []
        self._extract_structure(root, 0)
        return root

    def _extract_structure(self, element, level):
        """Recursively extract structure."""
        if element.tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            heading_level = int(element.tag[1])
            text = "".join(element.itertext())
            self.structure.append({"level": heading_level, "text": text, "element": element})

        for child in element:
            self._extract_structure(child, level + 1)


class StructureExtension(Extension):
    """Markdown extension to extract structure."""

    def extendMarkdown(self, md):
        """Register the tree processor."""
        self.processor = StructureExtractor(md)
        md.treeprocessors.register(self.processor, "structure", 15)


class PlanParser:
    """Parser for DEVELOPMENT_PLAN.md files."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self.md = markdown.Markdown(extensions=["extra", StructureExtension()])

    def parse_file(self, filepath: str | Path) -> Plan:
        """Parse a DEVELOPMENT_PLAN.md file and extract structured data.

        Args:
            filepath: Path to the DEVELOPMENT_PLAN.md file

        Returns:
            Plan object containing all extracted data

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is malformed
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Plan file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return self.parse_content(content)

    def parse_content(self, content: str) -> Plan:
        """Parse plan content from string.

        Args:
            content: Markdown content

        Returns:
            Plan object
        """
        # Convert markdown to HTML and extract structure
        self.md.convert(content)

        # Extract title (first H1)
        title = self._extract_title(content)

        # Extract executive summary
        executive_summary = self._extract_section(content, "Executive Summary")

        # Extract core principles
        core_principles = self._extract_core_principles(content)

        # Extract phases
        phases = self._extract_phases(content)

        # Extract quality metrics
        quality_metrics = self._extract_quality_metrics(content)

        # Extract risks
        risks = self._extract_risks(content)

        return Plan(
            title=title,
            executive_summary=executive_summary,
            core_principles=core_principles,
            phases=phases,
            quality_metrics=quality_metrics,
            risks=risks,
        )

    def _extract_title(self, content: str) -> str:
        """Extract the main title from content."""
        # Find first H1 heading
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled Plan"

    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract content from a specific section."""
        # Find section heading
        pattern = rf"^##\s+{re.escape(section_name)}\s*$"
        match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
        if not match:
            return None

        # Extract content until next ## heading
        start = match.end()
        next_heading = re.search(r"^##\s+", content[start:], re.MULTILINE)
        if next_heading:
            end = start + next_heading.start()
        else:
            end = len(content)

        section_content = content[start:end].strip()
        return section_content if section_content else None

    def _extract_core_principles(self, content: str) -> List[str]:
        """Extract core principles from the plan."""
        principles = []

        # Look for **Core Principles:** followed by bullet list
        principles_pattern = r"\*\*Core Principles:\*\*\s*\n((?:[-*]\s+\*\*.+\n?)+)"
        match = re.search(principles_pattern, content)

        if match:
            principles_text = match.group(1)
            # Extract bullet points with bold principle names (colon outside bold)
            # Format: - **Name**: Description
            principle_pattern = r"^[-*]\s+\*\*([^*]+)\*\*:\s*(.+)$"
            for principle_match in re.finditer(principle_pattern, principles_text, re.MULTILINE):
                principle_name = principle_match.group(1).strip()
                description = principle_match.group(2).strip()
                principles.append(f"{principle_name}: {description}")

        return principles

    def _extract_phases(self, content: str) -> List[Phase]:
        """Extract all phases from the plan."""
        phases: List[Phase] = []

        # Find all phase headings (## Phase N: Name)
        phase_pattern = r"^##\s+Phase\s+(\d+):\s+(.+)$"
        phase_matches = list(re.finditer(phase_pattern, content, re.MULTILINE))

        for i, match in enumerate(phase_matches):
            phase_number = int(match.group(1))
            phase_name = match.group(2).strip()

            # Extract phase content (until next phase or end)
            start = match.end()
            if i + 1 < len(phase_matches):
                end = phase_matches[i + 1].start()
            else:
                end = len(content)

            phase_content = content[start:end]

            # Extract week range from first line of phase content
            week_range = self._extract_week_range(phase_content.split("\n")[0])

            # Extract stages from phase content
            stages = self._extract_stages(phase_content, phase_number)

            phases.append(
                Phase(
                    phase_number=phase_number,
                    phase_name=phase_name,
                    week_range=week_range,
                    stages=stages,
                )
            )

        return phases

    def _extract_stages(self, phase_content: str, phase_number: int) -> List[Stage]:
        """Extract stages from a phase."""
        stages: List[Stage] = []

        # Find all stage headings (### Stage X.Y: Name (Week Y-Z))
        stage_pattern = r"^###\s+Stage\s+(\d+\.\d+):\s+(.+?)(?:\s+\(Week[s]?\s+([\d-]+)\))?$"
        stage_matches = list(re.finditer(stage_pattern, phase_content, re.MULTILINE))

        for i, match in enumerate(stage_matches):
            stage_number = match.group(1)
            stage_name = match.group(2).strip()
            week_range_match = match.group(3)

            # Extract stage content
            start = match.end()
            if i + 1 < len(stage_matches):
                end = stage_matches[i + 1].start()
            else:
                end = len(phase_content)

            stage_content = phase_content[start:end]

            # Week range from heading or content
            week_range = f"Week {week_range_match}" if week_range_match else self._extract_week_range(stage_content)
            objective = self._extract_objective(stage_content)
            key_activities = self._extract_list_items(stage_content, "Key Activities")
            deliverables = self._extract_list_items(stage_content, "Deliverables")
            validation_criteria = self._extract_list_items(stage_content, "Validation Criteria")
            technical_implementation = self._extract_technical_implementation(stage_content)

            # Create task from stage
            task = Task(
                id=f"phase{phase_number}-stage{stage_number}",
                title=stage_name,
                description=objective,
                phase=f"Phase {phase_number}",
                stage=f"Stage {stage_number}",
                week_range=week_range,
                objective=objective,
                key_activities=key_activities,
                deliverables=deliverables,
                validation_criteria=validation_criteria,
                technical_implementation=technical_implementation,
            )

            stages.append(
                Stage(
                    stage_number=stage_number,
                    stage_name=stage_name,
                    week_range=week_range,
                    objective=objective,
                    key_activities=key_activities,
                    deliverables=deliverables,
                    validation_criteria=validation_criteria,
                    technical_implementation=technical_implementation,
                    tasks=[task],
                )
            )

        return stages

    def _extract_week_range(self, content: str) -> Optional[str]:
        """Extract week range from content."""
        # Pattern: (Week 1-2) or (Weeks 3-6)
        match = re.search(r"\(Week[s]?\s+([\d-]+)\)", content)
        if match:
            return f"Week {match.group(1)}"
        return None

    def _extract_objective(self, content: str) -> str:
        """Extract objective from stage content."""
        # Look for **Objective**: ...
        match = re.search(r"\*\*Objective\*\*:\s*(.+?)(?:\n\n|\n\*\*)", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_list_items(self, content: str, section_name: str) -> List[str]:
        """Extract list items from a section."""
        items: List[str] = []

        # Find section heading with colon
        pattern = rf"\*\*{re.escape(section_name)}:\*\*"
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            return items

        # Extract content after heading until next **Section:** or end
        start = match.end()
        # Find the next bold section heading
        next_section = re.search(r"\n\n\*\*[A-Z]", content[start:])
        if next_section:
            end = start + next_section.start()
        else:
            end = len(content)

        section_content = content[start:end].strip()

        # Extract list items (- item or numbered items)
        for line in section_content.split("\n"):
            line = line.strip()
            # Match bullet points or numbered lists
            item_match = re.match(r"^[-*]\s+(.+)$", line)
            if item_match:
                item_text = item_match.group(1).strip()
                # Remove any markdown formatting
                item_text = re.sub(r"\*\*(.+?)\*\*", r"\1", item_text)
                items.append(item_text)

        return items

    def _extract_technical_implementation(self, content: str) -> Optional[str]:
        """Extract technical implementation section."""
        # Look for **Technical Implementation:** followed by code block
        match = re.search(
            r"\*\*Technical Implementation:\*\*\s*\n```python\s*\n(.+?)```",
            content,
            re.DOTALL,
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_quality_metrics(self, content: str) -> dict:
        """Extract quality metrics from the plan."""
        metrics = {}
        # Look for "Quality Metrics" or "Quality Metrics and Success Criteria" section
        section = self._extract_section(content, "Quality Metrics and Success Criteria")
        if not section:
            section = self._extract_section(content, "Quality Metrics")

        if section:
            # Extract coverage requirement
            coverage_match = re.search(r"[Tt]est coverage[:\s]+≥\s*(\d+)%", section)
            if coverage_match:
                metrics["test_coverage_minimum"] = int(coverage_match.group(1))
        return metrics

    def _extract_risks(self, content: str) -> List[dict]:
        """Extract risks from the plan."""
        risks: List[dict] = []
        section = self._extract_section(content, "Risk Management and Mitigation")
        if not section:
            section = self._extract_section(content, "High-Priority Risks")

        if section:
            # Look for numbered risk items with **Risk: Name**
            # Pattern matches: number, risk name, mitigation line(s), optional monitoring
            risk_pattern = r"(\d+)\.\s+\*\*Risk:\s*(.+?)\*\*\s*\n\s+-\s+Mitigation:\s*([^\n]+)"
            for match in re.finditer(risk_pattern, section):
                risk_name = match.group(2).strip()
                mitigation_text = match.group(3).strip()
                risks.append(
                    {
                        "risk_name": risk_name,
                        "description": "",
                        "priority": "high",
                        "mitigation": [mitigation_text],
                    }
                )

        return risks
