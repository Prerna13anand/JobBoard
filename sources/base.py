"""
Shared interface that every job source must implement.

Keeping this contract small (fetch_raw + normalize) is what lets jobs.py stay
source-agnostic: it just calls `run()` on each source and concatenates the
results, regardless of whether the underlying API is a simple REST endpoint
(Arbeitnow, RemoteOK, Jobicy) or an ATS board (Greenhouse, Lever) that needs
per-company requests.
"""

from abc import ABC, abstractmethod


class BaseJobSource(ABC):
    """Abstract base class for a single job source/provider."""

    #  Human-readable name, used in logging and error messages.
    name = "base"

    @abstractmethod
    def fetch_raw(self):
        """
        Fetch raw job postings from the source's API.

        Returns:
            A list of raw job records (dicts) in whatever shape the
            source's API returns them.
        """
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_job):
        """
        Convert a single raw job record into the project's standard schema:

            {
                "title": str,
                "company": str,
                "location": str,
                "url": str,
                "tags": list[str],
                "remote": bool,
                "posted": str,
            }
        """
        raise NotImplementedError

    def run(self):
        """
        Fetch and normalize all jobs from this source.

        Any failure here (network error, bad response, etc.) is caught and
        logged so that one broken source can't take down the whole
        aggregation run.
        """
        try:
            raw_jobs = self.fetch_raw()
        except Exception as exc:
            print(f"[{self.name}] failed to fetch jobs: {exc}")
            return []

        normalized_jobs = []
        for raw_job in raw_jobs:
            try:
                normalized_jobs.append(self.normalize(raw_job))
            except Exception as exc:
                print(f"[{self.name}] skipped a job due to normalize error: {exc}")

        print(f"[{self.name}] fetched {len(normalized_jobs)} jobs")
        return normalized_jobs
