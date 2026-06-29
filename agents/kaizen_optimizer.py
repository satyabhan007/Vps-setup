import json
import os

class KaizenAgent:
    def __init__(self, lakehouse_path):
        self.lakehouse_path = lakehouse_path # MinIO path

    def analyze_failures(self):
        """
        Scans the 'Human-Corrected' logs in the lakehouse to find 
        patterns where the AI failed but the human fixed it.
        """
        corrected_data = []
        # Read from MinIO/S3 bucket
        # For demo, we simulate reading a JSONL file of corrections
        for file in os.listdir(self.lakehouse_path):
            if file.endswith(".jsonl"):
                with open(os.path.join(self.lakehouse_path, file), 'r') as f:
                    for line in f:
                        corrected_data.append(json.loads(line))
        
        return self._cluster_failures(corrected_data)

    def _cluster_failures(self, data):
        """
        Groups similar failures to identify a 'Cluster' 
        (e.g., 50 patients struggled with 'Insurance' questions).
        """
        clusters = {}
        for entry in data:
            fail_type = entry.get("failure_type", "general")
            clusters[fail_type] = clusters.get(fail_type, 0) + 1
        return clusters

    def update_system_prompt(self, cluster_report):
        """
        Updates the global system prompt to prevent future occurrences 
        of the most common failure cluster.
        """
        top_failure = max(cluster_report, key=cluster_report.get)
        # Logic to append a 'Rule' to the system prompt:
        # "Rule: When patients ask about [top_failure], always refer to the Insurance PDF."
        return f"OPTIMIZATION: New rule added to handle {top_failure}"
