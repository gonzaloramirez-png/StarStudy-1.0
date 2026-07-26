from .dashboard import dev_dashboard
from .challenges import challenge_list, challenge_detail, challenge_create, submission_history
from .snippets import snippet_list, snippet_create, snippet_edit, snippet_delete
from .ranking import dev_ranking
from .health import health_dashboard
from .adr import adr_list, adr_detail, adr_create, adr_edit
from .api import (
    api_health_ping, api_challenge_today, api_submit,
    api_snippets, api_snippet_create, api_profile,
)
