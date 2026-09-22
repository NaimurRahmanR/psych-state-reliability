"""Benchmark V2 scenario families.

Twelve authored everyday, non-clinical social-evaluative situations. Each family
differs in the relationship involved, the *source* of interpretive ambiguity, the
plausible benign explanation, and the shape of later correction.

Motivation: V1 rendered every trajectory from a single hardcoded situation
("The organiser sent a brief reply to my request about the next meeting") and
varied only an activity noun, so all 120 calibration condition variants shared
one semantic frame. Surface text here is authored per family rather than
produced by substituting nouns into one sentence frame.

Nothing here is clinical. No text asserts what another person actually intended;
all appraisal text is written as the user's own reported interpretation, which is
the distinction the psychology specification requires.
"""
from __future__ import annotations

# Each family supplies:
#   context_phrase        - public activity label used in context statements
#   relationship          - who the other party is (diversity axis)
#   ambiguity_source      - what makes the situation readable two ways
#   situation             - turn-1 narrative (carries no appraisal and no emotion)
#   appraisal[value]      - wording variants, user-voiced, family-specific
#   confirming            - later evidence consistent with the negative reading
#   competing             - two readings held at once, unresolved
#   changed_circumstances - the situation itself moves on
#   contradiction         - two conflicting outside accounts + explicit uncertainty
#   supersession          - explicit user retraction of the earlier interpretation
#   second_topic          - an unrelated later topic, for the stale-state condition

FAMILIES = {
  "workplace_feedback": {
    "context_phrase": "a work project I am reviewing feedback on",
    "relationship": "line_manager",
    "ambiguity_source": "terse_written_feedback",
    "situation": "My manager left three one-word comments on the report I spent a fortnight writing. The only full sentence was 'we'll discuss'.",
    "appraisal": {
      "negative_judgment": [
        "I take those one-word comments to mean my manager thinks the work was poor.",
        "My reading is that 'we'll discuss' is how she signals something went badly wrong.",
        "I understand the lack of any real comment as a judgment that the report was not worth engaging with."],
      "uncertain_meaning": [
        "I genuinely cannot tell whether three one-word comments mean criticism or just haste.",
        "I do not know how to read 'we'll discuss'; it could be anything.",
        "The comments are too short for me to work out what she actually thought."],
      "situational_explanation": ["I now read the short comments as a sign of how compressed her week was, not a verdict on the report."],
      "resolved": ["The review is closed and the report went forward; this is not something I am carrying now."],
      "unknown": ["I have not worked out what I make of the comments."]},
    "confirming": "In the team meeting she skipped my section entirely and moved to the next item.",
    "competing": "Two readings still sit side by side for me: either the report underwhelmed her, or she was clearing a backlog at speed. I have no way to choose between them.",
    "changed_circumstances": "The project was reassigned to a different team this week, so the report is no longer mine to defend.",
    "contradiction": "A colleague who was in the review told me the report was described as solid. Another colleague told me it was flagged as needing rework. Both were in the room. I cannot reconcile those two accounts and I no longer know what the comments meant.",
    "supersession": "I want to correct what I said earlier. My manager explained she was reviewing eleven documents in two days and commented at that speed on all of them. I no longer read those comments as a judgment of my work.",
    "second_topic": {"label": "planning a house move", "text": "That report is behind me now. Today I want to talk about something unrelated: I have started organising a house move and I have not yet worked out what I think about it."}},

  "academic_collaboration": {
    "context_phrase": "a joint paper I am writing with a collaborator",
    "relationship": "co_author",
    "ambiguity_source": "unexplained_silence_on_a_draft",
    "situation": "I sent my co-author the full draft eleven days ago. She has been posting about other projects since, and has not mentioned mine.",
    "appraisal": {
      "negative_judgment": [
        "I interpret eleven days of silence as her having decided the draft is not worth her time.",
        "My reading is that she has quietly lost interest in the collaboration.",
        "I take the silence, alongside her posting about other work, as a judgment on what I sent."],
      "uncertain_meaning": [
        "I cannot tell whether eleven days of silence means disinterest or an ordinary backlog.",
        "The silence is genuinely ambiguous to me and I have stopped trying to decode it.",
        "I do not know what her not replying means."],
      "situational_explanation": ["I now understand the delay as a workload problem on her side rather than a verdict on the draft."],
      "resolved": ["We have submitted the paper; the question of what the silence meant no longer applies."],
      "unknown": ["I have not settled on an interpretation of the silence."]},
    "confirming": "She has now missed the second deadline we agreed, again without mentioning the draft.",
    "competing": "I hold two explanations at once and cannot rank them: either the draft disappointed her, or she is simply overloaded. Both fit everything I have observed.",
    "changed_circumstances": "My supervisor has reassigned the paper to a different collaboration, so the original arrangement has lapsed.",
    "contradiction": "Her postdoc told me she has been reading my draft closely and taking notes. A shared colleague told me she has written the project off. I cannot resolve these conflicting accounts and I do not know what the silence means now.",
    "supersession": "I need to correct my earlier interpretation. She was on fieldwork with no reliable connection for the whole period. I no longer read the silence as disinterest.",
    "second_topic": {"label": "starting a running club", "text": "The paper is settled now. I want to raise something different today: I joined a running club this week and I have not yet formed a view about how it went."}},

  "friendship_delay": {
    "context_phrase": "a long friendship",
    "relationship": "close_friend",
    "ambiguity_source": "unanswered_personal_message",
    "situation": "I told a friend of fourteen years something difficult about my week. He read the message on Tuesday and has not replied.",
    "appraisal": {
      "negative_judgment": [
        "I read his not replying to something that personal as him withdrawing from the friendship.",
        "My interpretation is that he did not think what I told him was worth responding to.",
        "I take the read receipt plus the silence as a deliberate choice not to engage with me."],
      "uncertain_meaning": [
        "I do not know what it means that he read it and said nothing.",
        "I cannot decide whether the silence is about me or about him.",
        "His not replying is genuinely unreadable to me."],
      "situational_explanation": ["I now see the silence as being about what he was dealing with that week, not about the friendship."],
      "resolved": ["We have spoken since and the whole thing has passed."],
      "unknown": ["I have not formed an interpretation of the silence yet."]},
    "confirming": "He replied to a group message about football two days later, still without answering mine.",
    "competing": "Both readings still feel live: he may be pulling away, or he may have frozen because he did not know what to say. I cannot tell which.",
    "changed_circumstances": "He has moved abroad for work, so the situation I was worried about no longer exists in the same form.",
    "contradiction": "His partner told me he had been upset and did not know how to answer. His brother told me he had simply forgotten. Those two accounts do not fit together and I do not know what the silence meant.",
    "supersession": "I want to revise what I said. He had been dealing with a family emergency all week. I no longer take the silence as a withdrawal from the friendship.",
    "second_topic": {"label": "an adult education course", "text": "That is resolved now. Something separate: I have enrolled on an evening course starting this week and I have not yet decided how I read it."}},

  "social_exclusion": {
    "context_phrase": "a group of friends I see regularly",
    "relationship": "friendship_group",
    "ambiguity_source": "omission_from_a_gathering",
    "situation": "Photographs from a dinner on Saturday appeared online. Six people from our usual group were there. I had not been told it was happening.",
    "appraisal": {
      "negative_judgment": [
        "I read not being told as a decision by the group that I am not really one of them.",
        "My interpretation is that they chose the six people they actually wanted there.",
        "I take my absence from that dinner as evidence of where I sit in the group."],
      "uncertain_meaning": [
        "I cannot work out whether I was left out deliberately or simply missed.",
        "I do not know what the omission means.",
        "It is unclear to me whether this was a decision about me at all."],
      "situational_explanation": ["I now understand it as a small gathering organised at short notice rather than a judgment about my place in the group."],
      "resolved": ["I have been to two things with them since and this has stopped mattering."],
      "unknown": ["I have not settled on what I think the omission means."]},
    "confirming": "A second gathering happened this week and again I heard about it afterwards.",
    "competing": "I can argue it both ways and cannot land: either I am being edged out, or it was a six-seat table and nothing more. Both remain plausible.",
    "changed_circumstances": "Two of them have moved away and the group no longer meets in that form.",
    "contradiction": "One person told me the guest list was deliberately kept small and I was not on it. Another told me they had assumed I was already invited and were surprised I was not there. I cannot make these accounts agree and I no longer know what happened.",
    "supersession": "I should correct my earlier reading. It was a booking for six made the same afternoon, and three other regulars were not there either. I no longer take it as a judgment about my place in the group.",
    "second_topic": {"label": "a new caring responsibility", "text": "That has settled. Today is about something else entirely: I have taken on helping a neighbour with her weekly shop and I have not yet worked out what I make of the arrangement."}},

  "volunteering_role": {
    "context_phrase": "a community kitchen I volunteer at",
    "relationship": "volunteer_coordinator",
    "ambiguity_source": "reassignment_without_explanation",
    "situation": "I have run the Thursday serving shift at the community kitchen for two years. This month's rota has me on washing up and someone newer on serving.",
    "appraisal": {
      "negative_judgment": [
        "I read being moved to washing up as the coordinator deciding I was not good at the serving role.",
        "My interpretation is that someone complained about how I ran the shift.",
        "I take the reassignment as a quiet way of telling me I was not wanted at the front."],
      "uncertain_meaning": [
        "I cannot tell whether the rota change is about my performance or about nothing at all.",
        "I do not know why the change was made.",
        "The reassignment is ambiguous to me and no reason was given."],
      "situational_explanation": ["I now understand the change as part of a rotation policy rather than a judgment about how I ran the shift."],
      "resolved": ["I am back on serving from next month and the question has gone away."],
      "unknown": ["I have not decided what I think about being moved."]},
    "confirming": "The coordinator has now moved me again, to a shift I did not ask for, still without saying why.",
    "competing": "Two explanations stay equally live: either someone raised a concern about me, or the rota is simply being rotated. I cannot distinguish them from what I know.",
    "changed_circumstances": "The kitchen has merged with another project and the whole rota structure has been rebuilt from scratch.",
    "contradiction": "One of the long-standing volunteers told me there had been a complaint about my shift. The coordinator's deputy told me the rota rotates on a fixed cycle and nobody said anything about me. These accounts contradict each other and I do not know which is true.",
    "supersession": "I want to correct what I said. The kitchen introduced a six-month rotation for every role this year and everyone has moved. I no longer read my reassignment as a judgment about my work.",
    "second_topic": {"label": "a disagreement about a shared fence", "text": "The rota question is closed. I want to bring up something unconnected: there is a disagreement with a neighbour about a shared fence and I have not yet worked out my interpretation of it."}},

  "hobby_critique": {
    "context_phrase": "a writing group I attend",
    "relationship": "peer_group_member",
    "ambiguity_source": "ambiguous_severity_of_critique",
    "situation": "At the writing group on Monday, a member spent eleven minutes on what was not working in my chapter and about thirty seconds on what was.",
    "appraisal": {
      "negative_judgment": [
        "I read that ratio as him thinking the chapter has nothing much going for it.",
        "My interpretation is that eleven minutes of problems is a verdict, not feedback.",
        "I take the imbalance as meaning he does not rate my writing."],
      "uncertain_meaning": [
        "I cannot tell whether that was unusually harsh or just how he gives feedback.",
        "I do not know how to weigh what he said.",
        "The length of the critique is ambiguous to me; it might mean engagement or dismissal."],
      "situational_explanation": ["I now read the length of his critique as the group's standard format rather than a verdict on my writing."],
      "resolved": ["I have rewritten the chapter and moved on from that session."],
      "unknown": ["I have not decided what I make of the feedback."]},
    "confirming": "He gave the next writer four minutes of problems and a long stretch on what worked.",
    "competing": "I hold both at once: either he thinks little of the chapter, or detailed critique is how he shows he took it seriously. Neither reading has pulled ahead.",
    "changed_circumstances": "The group has changed facilitator and the critique format has been replaced entirely.",
    "contradiction": "Another member told me afterwards that he had been unusually hard on me. The facilitator told me his critique was the same length he gives everyone and read as engaged. I cannot reconcile these and I no longer know how to take it.",
    "supersession": "I need to correct my earlier interpretation. The group runs a fixed format where problems are covered first and at length for every piece. I no longer read the eleven minutes as a judgment of my writing.",
    "second_topic": {"label": "a change in working hours", "text": "The chapter is rewritten and that is done. Separately, my working hours have changed this month and I have not yet formed a view on it."}},

  "family_plans": {
    "context_phrase": "an arrangement with a family member",
    "relationship": "sibling",
    "ambiguity_source": "repeated_cancellation",
    "situation": "My sister cancelled our visit for the second time, four hours before, by text. We had arranged it eight weeks ago.",
    "appraisal": {
      "negative_judgment": [
        "I read two cancellations in a row as her showing that seeing me is low on her list.",
        "My interpretation is that she cancels on me because she knows I will not make a fuss.",
        "I take the four hours' notice as a measure of how much the visit mattered to her."],
      "uncertain_meaning": [
        "I cannot tell whether this is about me or about how her life is running at the moment.",
        "I do not know what to make of the second cancellation.",
        "Two cancellations could mean anything and I have not been able to read it."],
      "situational_explanation": ["I now understand the cancellations as her shift pattern rather than a statement about how much she wants to see me."],
      "resolved": ["We saw each other last weekend and this has stopped being an issue."],
      "unknown": ["I have not worked out how I read the cancellations."]},
    "confirming": "She then posted pictures from a day out with friends on the afternoon she had cancelled.",
    "competing": "Both explanations survive everything I know: either I am genuinely low on her list, or her rota keeps collapsing at short notice. I cannot choose.",
    "changed_circumstances": "She has moved to a job with fixed hours, so the pattern that caused this has ended.",
    "contradiction": "Our mother told me she had been asking about coming down for weeks. Our cousin told me she had said she was avoiding the trip. Those accounts do not fit together and I do not know what the cancellations meant.",
    "supersession": "I want to revise what I said earlier. Both cancellations were emergency shift call-ins that she could not refuse. I no longer read them as a statement about how much she wants to see me.",
    "second_topic": {"label": "a community allotment", "text": "That is behind us now. A separate matter: I have taken on an allotment plot this month and I have not yet decided what I think of it."}},

  "recognition_ambiguity": {
    "context_phrase": "a team project that was publicly announced",
    "relationship": "project_lead",
    "ambiguity_source": "non_acknowledgement_in_public",
    "situation": "The launch announcement went out on Friday. It named four people. I did eight months on that project and I was not one of them.",
    "appraisal": {
      "negative_judgment": [
        "I read not being named as a decision that my eight months did not count as a real contribution.",
        "My interpretation is that the lead deliberately chose whose names went in.",
        "I take the omission as a public statement about my standing on the project."],
      "uncertain_meaning": [
        "I cannot tell whether the list was a judgment or a template.",
        "I do not know why those four names and not mine.",
        "The omission is genuinely unclear to me."],
      "situational_explanation": ["I now read the list as the standard format for naming workstream leads rather than a judgment about my contribution."],
      "resolved": ["A corrected announcement went out and the matter is closed."],
      "unknown": ["I have not settled on what the omission means."]},
    "confirming": "The follow-up post named two more people, and again not me.",
    "competing": "I can hold either reading: a deliberate omission, or a template that lists only workstream leads. Nothing I know separates them.",
    "changed_circumstances": "The project has been folded into a different programme and the original announcement has been withdrawn.",
    "contradiction": "One person on the project told me my name was taken off the list late. The communications officer told me the template only ever lists four workstream leads and nobody was removed. I cannot reconcile those and I no longer know what the omission meant.",
    "supersession": "I should correct my earlier reading. The announcement template names workstream leads only, and two other long-standing contributors were also not listed. I no longer take the omission as a judgment about my contribution.",
    "second_topic": {"label": "a first-time public talk", "text": "The announcement is dealt with. Today I want to raise something different: I have been asked to give a talk for the first time and I have not yet worked out what I think about it."}},

  "neighbour_arrangement": {
    "context_phrase": "an arrangement with a neighbour",
    "relationship": "neighbour",
    "ambiguity_source": "withdrawal_from_a_shared_arrangement",
    "situation": "For three years my neighbour and I have taken turns on the school run. On Sunday she texted that she will be making her own arrangements from now on.",
    "appraisal": {
      "negative_judgment": [
        "I read the text as her having decided she no longer wants to be associated with us.",
        "My interpretation is that something about how we do the run annoyed her and she did not say so.",
        "I take ending a three-year arrangement by text as a judgment about us."],
      "uncertain_meaning": [
        "I cannot tell whether this is about us or about her own schedule.",
        "I do not know what ending it by text is meant to convey.",
        "The message is too short for me to interpret."],
      "situational_explanation": ["I now understand the change as her new working hours rather than a judgment about us."],
      "resolved": ["The children have changed schools and the arrangement would have ended anyway."],
      "unknown": ["I have not worked out what I make of the message."]},
    "confirming": "She has since stopped saying hello when we pass on the street.",
    "competing": "Two readings remain open: either something about us put her off, or her hours changed and the run stopped fitting. I cannot tell which.",
    "changed_circumstances": "We are moving out of the area next month, so the arrangement would have ended regardless.",
    "contradiction": "Another neighbour told me she had been unhappy about the arrangement for months. Her own mother told me her shift pattern had changed and she was sorry to stop. These two accounts conflict and I do not know what the message meant.",
    "supersession": "I want to correct what I said. Her hours moved to an earlier start and the school run no longer fits them. I no longer read the message as a judgment about us.",
    "second_topic": {"label": "returning to study", "text": "The school run is sorted now. Something unrelated: I have applied to go back to study part time and I have not yet formed an interpretation of how that is going."}},

  "mentoring_mismatch": {
    "context_phrase": "a mentoring arrangement",
    "relationship": "mentor",
    "ambiguity_source": "reduced_investment_of_time",
    "situation": "My mentor has moved our hour to thirty minutes and rescheduled it three times this term. Last session she took a call partway through.",
    "appraisal": {
      "negative_judgment": [
        "I read the halved sessions and the rescheduling as her regretting taking me on.",
        "My interpretation is that she has concluded I am not worth the hour.",
        "I take her answering a call mid-session as a measure of how much attention I warrant."],
      "uncertain_meaning": [
        "I cannot tell whether this is about me or about her term.",
        "I do not know what the shortened sessions are meant to signal.",
        "The pattern is ambiguous and I have not been able to read it."],
      "situational_explanation": ["I now read the shortened sessions as her teaching load this term rather than a judgment about me."],
      "resolved": ["The mentoring arrangement has formally ended as planned and this no longer applies."],
      "unknown": ["I have not decided what I make of the change."]},
    "confirming": "She cancelled this week's session forty minutes before it was due to start.",
    "competing": "Both accounts stay standing: either she regrets the commitment, or her term has overrun her. I have nothing that separates them.",
    "changed_circumstances": "I have been assigned a different mentor for next term, so the arrangement I was worried about has ended.",
    "contradiction": "A fellow mentee told me she had said she was overcommitted and wanted to drop someone. The programme administrator told me she had asked to extend my mentoring by a term. I cannot make these agree and I no longer know how to read the shortened sessions.",
    "supersession": "I need to correct my earlier interpretation. She took on two additional modules this term and every one of her mentees moved to thirty minutes. I no longer read it as being about me.",
    "second_topic": {"label": "a household budgeting change", "text": "The mentoring question is closed. Today is about something separate: we have changed how we run the household budget and I have not yet worked out what I think of it."}},

  "online_community": {
    "context_phrase": "an online community I post in",
    "relationship": "forum_moderator",
    "ambiguity_source": "removal_without_stated_reason",
    "situation": "A post I spent an evening writing was removed from the forum within an hour. No reason was given and the message to the moderators has not been answered.",
    "appraisal": {
      "negative_judgment": [
        "I read the removal plus the silence as the moderators deciding I am not welcome there.",
        "My interpretation is that someone on the team objected to me personally.",
        "I take an hour's turnaround and no explanation as a judgment about me rather than the post."],
      "uncertain_meaning": [
        "I cannot tell whether this was a rule, a filter, or a person.",
        "I do not know why the post was removed.",
        "With no reason given, the removal is unreadable to me."],
      "situational_explanation": ["I now understand the removal as an automated filter rather than a decision about me."],
      "resolved": ["The post has been restored and the question no longer arises."],
      "unknown": ["I have not settled on an interpretation of the removal."]},
    "confirming": "A second post of mine was removed this morning, again with no reason given.",
    "competing": "Two explanations stay equally plausible: a moderator objecting to me, or an automated filter catching a link. I cannot rule either out.",
    "changed_circumstances": "The forum has closed to new posts while it migrates, so the situation has moved on.",
    "contradiction": "One moderator replied that the post broke a self-promotion rule. Another moderator replied that it was caught by an automated filter in error. Those two answers contradict each other and I do not know why it was removed.",
    "supersession": "I want to correct my earlier reading. The removal was an automated link filter and the post has been reinstated. I no longer take it as a decision about me.",
    "second_topic": {"label": "a change in caring hours", "text": "The post is restored and that is finished. A different matter: my caring hours have changed this month and I have not yet decided what I make of it."}},

  "team_selection": {
    "context_phrase": "a recreational sports team",
    "relationship": "team_captain",
    "ambiguity_source": "non_selection_for_a_fixture",
    "situation": "I was not named in the squad for Saturday's fixture. I have trained every week this season and two people who train less often were named.",
    "appraisal": {
      "negative_judgment": [
        "I read not being named as the captain deciding I am not good enough for the side.",
        "My interpretation is that training every week counts for nothing with him.",
        "I take being left out ahead of two less regular players as a judgment about my ability."],
      "uncertain_meaning": [
        "I cannot tell whether this is about ability or about rotation.",
        "I do not know why I was not named.",
        "The team sheet is ambiguous to me and no reason was given."],
      "situational_explanation": ["I now read the team sheet as the squad rotation policy rather than a judgment about my ability."],
      "resolved": ["I played the following two fixtures and this has stopped being a question."],
      "unknown": ["I have not worked out how I read the team sheet."]},
    "confirming": "I was left out again this week and the same two players started.",
    "competing": "I can hold both: either he rates me below them, or the club rotates the squad on a fixed cycle. Nothing I have seen decides it.",
    "changed_circumstances": "The league has restructured and our side has been merged with another, so selection starts from scratch.",
    "contradiction": "The assistant coach told me the captain had concerns about my form. The club secretary told me selection follows a published rotation and form was never raised. I cannot reconcile those accounts and I no longer know why I was left out.",
    "supersession": "I should correct what I said earlier. The club runs a published rotation that guarantees everyone a set number of starts, and three other regulars also sat out. I no longer read it as a judgment about my ability.",
    "second_topic": {"label": "a new shift at work", "text": "Selection is settled now. Separately, I have moved onto a new shift pattern at work this week and I have not yet formed a view about it."}},
}

_REQUIRED = ("context_phrase", "relationship", "ambiguity_source", "situation", "appraisal",
             "confirming", "competing", "changed_circumstances", "contradiction",
             "supersession", "second_topic")
APPRAISAL_VALUES = ("negative_judgment", "uncertain_meaning", "situational_explanation", "resolved", "unknown")

for _name, _f in FAMILIES.items():
    _missing = [k for k in _REQUIRED if k not in _f]
    if _missing:
        raise ValueError(f"Family {_name} missing {_missing}")
    if set(_f["appraisal"]) != set(APPRAISAL_VALUES):
        raise ValueError(f"Family {_name} has wrong appraisal value set")
    for _v in APPRAISAL_VALUES:
        if not _f["appraisal"][_v] or not all(isinstance(t, str) and t.strip() for t in _f["appraisal"][_v]):
            raise ValueError(f"Family {_name} has empty appraisal text for {_v}")
    if set(_f["second_topic"]) != {"label", "text"}:
        raise ValueError(f"Family {_name} has a malformed second_topic")

FAMILY_IDS = tuple(sorted(FAMILIES))
