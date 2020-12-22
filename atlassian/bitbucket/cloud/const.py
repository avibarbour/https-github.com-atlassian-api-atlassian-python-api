""" Bitbucket Cloud constants """

# Configuration
CONF_TIMEFORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"

# Pull Request
PR_MERGE_COMMIT = "merge_commit"
PR_MERGE_SQUASH = "squash"
PR_MERGE_FF = "fast_forward"
PR_MERGE_STRATEGIES = [
    PR_MERGE_COMMIT,
    PR_MERGE_SQUASH,
    PR_MERGE_FF,
]
PR_STATE_OPEN = "OPEN"
PR_STATE_DECLINED = "DECLINED"
PR_STATE_MERGED = "MERGED"
PR_STATE_SUPERSEDED = "SUPERSEDED"

# Pull Request Participant
PRP_ROLE_REVIEWER = "REVIEWER"
PRP_ROLE_PARTICIPANT = "PARTICIPANT"
PRP_CHANGES_REQUESTED = "changes_requested"
PRP_APPROVED = "approved"
