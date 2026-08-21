class TeamError(Exception):
    status_code = 400
    error_code = "TEAM_ERROR"
    detail = "Team operation failed."


class TeamNotFoundError(TeamError):
    status_code = 404
    error_code = "TEAM_NOT_FOUND"
    detail = "Team does not exist for this hackathon."


class TeamFullError(TeamError):
    status_code = 409
    error_code = "TEAM_FULL"
    detail = "Team has reached its maximum number of members."


class TeamsDisabledError(TeamError):
    status_code = 409
    error_code = "TEAMS_DISABLED"
    detail = "Teams are disabled for this hackathon."


class TeamNameAlreadyExistsError(TeamError):
    status_code = 409
    error_code = "TEAM_NAME_ALREADY_EXISTS"
    detail = "A team with this name already exists for this hackathon."


class TeamJoinCodeGenerationError(TeamError):
    status_code = 503
    error_code = "TEAM_JOIN_CODE_GENERATION_FAILED"
    detail = "A unique team join code could not be generated. Please try again."
