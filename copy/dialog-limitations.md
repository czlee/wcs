# Limitations dialog

<!-- Source: site/src/lib/components/Limitations.svelte (body), ExplorePage.svelte (title, button).
     Opens from the top-bar warning button and the footer link, and after the About dialog on a first visit.
     Until the reader clicks the button once (remembered in the browser), it can't be closed any other way.
     {…} are filled in from the data. -->

**Small heading above the title:** Before you read anything into this
**Title:** Reasons these comparisons might mislead

**Alert box:** **Wait! Before you read too much into this…** These comparisons have limits that can change what a difference between levels means.

- **This is exploratory.** It describes how much judges' rankings differ, by level. It doesn't explain why. Apart from a first-pass chance correction of the top-3 metrics (below), nothing on this site has been adjusted for the other differences between levels.

- **Levels differ in panel size and field size, and most of these metrics depend on both.** Kendall's W falls with more judges even if they're just as consistent; the rank-spread metrics grow with the field; and two judges' top 3s overlap more by chance in a smaller final. The top-3 charts subtract that chance level, a naive first-pass correction that doesn't remove every effect of field size, and leave out finals of 5, where any two top 3s must share someone. For example, Jack & Jill Novice finals here average about 13 competitors, All-Star finals about 8. Some or all of a difference between levels could come from this.
  <!-- The "13" and "8" are hard-coded; they should be checked against the data. -->

- **Regions differ in more than geography.** Panel and field sizes vary between regions, and so does the site that most of a region's scoresheets come from, so a difference between regions might come from either.

- **Scoresheets aren't independent.** The same judges sit on many panels. The error bars assume independence, so they're probably too narrow. The interval method itself (mean ± 1.96 standard errors) is provisional.

- **Levels are read from division names** by keyword. Combined divisions (e.g. "All-Star/Champions") count as the higher level, and invitational or differently-named divisions may be misfiled.

- **Not every event.** Only finals published on scoring.dance, eepro.com or danceconvention.net, with events from {first date} to {last date}. Finals with tied or incomplete rankings, fewer than 3 judges or fewer than 5 competitors are left out. Non-WCS divisions are filtered out by keyword, so a few might remain.

- **Finals, and rankings only.** This uses each judge's ranking of the finalists, not raw scores (where a scoresheet has them) or the final relative-placement result.

- **Some groups are small:** the smallest has only {N} scoresheets.
  <!-- {N} = the smallest count of scoresheets in any format × level. -->

- **Disagreement isn't error.** Judges are meant to use their own judgement, and nothing here says which judge was "right". This site doesn't rate individual judges. Names are shown only so that you can check the numbers against the published scoresheets.

**Button (shown until clicked once):** I understand and promise to take care with interpreting this
