`pm help` is the whole route table. It works without a store.

  $ pm help
  pm keeps this repo's tickets in .pm/. Bare `pm` shows what you hold and what is ready.
  Leave out [id] to mean the ticket you hold. One verb in detail: pm help <verb>

    take [id]             take the top ready ticket, or the one named, and print it
    note [id] "text"      add a note
    done [id] -m "text"   finish it
    park [id] -m "text"   stop with work unfinished and say what it waits on
    drop [id]             give it back untouched
    hold [id] -m "text"   keep it across a pause
    new "title"           file a ticket and print its id
    edit id               change title, body, priority, labels or epic
    link a blocks b       order two tickets; or: link a related b
    unlink a b            remove the links between two tickets
    reopen id             make a done or parked ticket open again
    show [id]             one ticket with its links and notes
    ls [words]            list: ready mine open taken parked done all epics under:id label:x, or text
    get id field          print one field per line, for scripts
    log [id]              print the raw events
    emit id ns.name k=v   record a plugin event
    init prefix           start a store in this directory
    stores                list every store on this machine
    doctor                check this store
    restore               bring back a lost log from its git backup
    import                fill a new log from an old tickets.jsonl
    hook event            print what an agent harness should inject

One verb's help is its usage line and a few sentences.

  $ pm help take
  usage: pm take [id ...] [--force] [--as name] [--dry-run]

  Take a ticket and print it. With no id, take the top of `pm ls ready`.
  Taking a ticket you already hold prints it again. Taking a parked ticket resumes it.
  --force takes a ticket that is blocked or that someone else holds. Use it only
  when the operator says so.
  --as records another name as the holder, for a named worker.
  --dry-run checks and changes nothing.

A wrong verb costs one line, never a help dump.

  $ pm clam
  pm: no verb "clam". Closest: claim. All verbs: pm help
  [2]
  $ pm xyzzy
  pm: no verb "xyzzy". All verbs: pm help
  [2]

The old verb names are accepted.

  $ pm init t >/dev/null
  $ pm create "old names still work"
  t-1
  $ pm claim t-1 >/dev/null && pm close t-1 -m "done the old way"
  t-1 done
  $ pm list all
  t-1  P2  done  old names still work
