`import` fills a new log from a spec v2 store. Old ids are kept; new tickets get short ones.

  $ mkdir .pm && cp "$FIXTURES"/v2/* .pm/ && pm import
  imported 4 tickets: 1 open, 1 taken, 1 parked, 1 done
  $ pm stores
  ol  $T/work

The claim in the fixture carries this session's token, so the ticket is still yours.

  $ pm
  yours:
    ol-cccccc  P1  taken  tag the commit  @claude
  parked:
    ol-dddddd  P2  parked  announce the release
  $ pm show ol-cccccc
  ol-cccccc  P1  taken  tag the commit  @claude
  under: ol-aaaaaa release 1.0
  related: ol-dddddd
  labels: release

  Use an annotated tag.

Notes keep their dates and kinds. Edit-trail notes are left behind.

  $ pm show ol-bbbbbb
  ol-bbbbbb  P2  done  write the changelog
  under: ol-aaaaaa release 1.0
  findings: none

  notes:
    2025-12-01 import [worker-return]: merged in abc123
  $ pm show ol-dddddd
  ol-dddddd  P2  parked  announce the release
  related: ol-cccccc

  notes:
    2025-12-02 import [park]: waits on the tag
  $ pm show ol-aaaaaa
  ol-aaaaaa  P2  open  release 1.0 [epic]
  children: 1 taken, 1 done
    ol-cccccc  P1  taken  tag the commit  @claude

  $ pm new "next ticket"
  ol-5
  $ pm import
  pm: this store already has events. Import only fills an empty log.
  [1]
