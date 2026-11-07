# HLTV fixtures

Real pages, saved unmodified, are the parser's regression tests. Fill them with
(one live request each, then cached for 24 h):

```bash
cs2shorts hltv https://www.hltv.org/matches/2400008/the-mongolz-vs-natus-vincere-iem-beijing-2026 --save-fixture tests/fixtures/hltv/match_mongolz_navi.html
cs2shorts hltv <a second match URL> --save-fixture tests/fixtures/hltv/match_second.html
cs2shorts hltv <a news URL that embeds a Twitch clip> --save-fixture tests/fixtures/hltv/news_clip.html
```

Then fill in the `None` values in `REAL` at the top of `tests/test_parse_match.py` by
reading the page (map count, highlight count, a few titles). Tests for missing fixtures or
`None` values are skipped.

`synthetic/` holds hand-written pages that mirror HLTV's markup so the parser is tested
before real fixtures exist. They are not real data.
