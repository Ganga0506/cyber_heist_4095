"""Coin rewards and hint inventory for playable challenges."""

from sqlalchemy import and_, case, func

from models import Mission, Puzzle, PuzzleAttempt

# Mission order and puzzle order identify each challenge across database seeds.
CHALLENGES = {
    (1, 1): (
        6, (3, 5, 8),
        ("Run the starter and compare the test outputs.",
         "Replace the quoted example with the variable encoded. Leave the variable unquoted.",
         "Enter decode64(encoded) to decode the current test input."),
    ),
    (1, 2): (
        9, (4, 7, 10),
        ("Compare the two domains using ==.",
         "Call lower on each variable before comparing them. Both sides can contain uppercase letters.",
         "Use lower(sender_domain) == lower(trusted_domain)."),
    ),
    (2, 1): (
        12, (5, 9, 13),
        ("Separate the status line, headers, and body.",
         "Find the line that starts with X-Access-Key.",
         "Copy only the value after the colon, including its hyphens."),
    ),
    (2, 2): (
        15, (6, 11, 16),
        ("The three lines each end with a response status.",
         "Exclude the health check and any line with status 401.",
         "Copy the method and path of the remaining 200 line, leaving off its time and status."),
    ),
    (5, 1): (
        18, (7, 13, 19),
        ("You need one token from each earlier mission.",
         "Use the decoded access note before the X-Access-Key value.",
         "Join the two values with just one hyphen and keep their existing internal hyphens."),
    ),
    (5, 2): (
        21, (8, 15, 22),
        ("Look for the option that contains the incident and protects evidence.",
         "Discard options that erase evidence or ignore the event.",
         "Choose the label that isolates the machine, preserves evidence, and reports the issue."),
    ),
}


def challenge(mission, puzzle):
    return CHALLENGES.get((mission.mission_order, puzzle.puzzle_order), (0, (), ())) if mission.is_mvp else (0, (), ())


def puzzle_reward_totals(db, user_id=None):
    solved_query = db.query(PuzzleAttempt.user_id, PuzzleAttempt.puzzle_id).filter(PuzzleAttempt.is_correct.is_(True))
    if user_id is not None:
        solved_query = solved_query.filter(PuzzleAttempt.user_id == user_id)
    solved = solved_query.distinct().subquery()
    reward = case(*[
        (and_(Mission.mission_order == mission_order, Puzzle.puzzle_order == puzzle_order), entry[0])
        for (mission_order, puzzle_order), entry in CHALLENGES.items()
    ], else_=0)
    return (
        db.query(solved.c.user_id, func.sum(reward).label("coins"))
        .join(Puzzle, Puzzle.id == solved.c.puzzle_id)
        .join(Mission, Mission.id == Puzzle.mission_id)
        .filter(Mission.is_mvp.is_(True))
        .group_by(solved.c.user_id)
    )
