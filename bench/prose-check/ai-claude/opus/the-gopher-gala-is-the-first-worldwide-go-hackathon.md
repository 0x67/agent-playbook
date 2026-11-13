# The Gopher Gala is the first worldwide Go hackathon

Most hackathons share a familiar shape: a rented hall, long tables, too much pizza, and a crowd drawn from one city. The Gopher Gala breaks that pattern. It's the first hackathon dedicated to Go that is open to anyone, anywhere. For 48 hours, starting January 23, 2015, Go programmers around the world will build projects from their own desks and kitchen tables and submit their work online.

Several of our engineers have signed up. This post explains what the Gopher Gala is, why its format suits Go well, and what we've learned about getting a useful project done in a weekend.

## How it works

The format is simple:

- **Teams are small.** You can enter alone or with a few collaborators, who don't need to share a city or a time zone.
- **The clock is global.** Everyone starts and stops at the same moment, whatever their local time. For some people the event starts on a Friday afternoon. For others it starts in the middle of the night.
- **Code lives on GitHub.** Each team builds in a repository, so the judges can review everything from the first commit to the last.
- **Go is the point.** Projects must be written primarily in Go, and the work has to happen during the event window.

Members of the Go community judge the finished projects. They look at how original the idea is, how well it's built, and whether it actually works. Check the official rules before you start, because they cover details that are easy to overlook in the rush of the first hour.

## Why Go suits a distributed hackathon

Running a hackathon over the internet would be painful in many ecosystems. Go avoids most of that pain, for a few reasons:

**Setup is fast.** A teammate on another continent can clone the repo and run `go build`. There's no long environment setup and no "works on my machine" debugging at 3 a.m.

**gofmt ends style debates.** When four people who have never worked together share a codebase, formatting arguments are a real distraction. With `gofmt`, there's nothing to argue about. Everyone's code looks the same, and diffs only show real changes.

**The standard library is large.** HTTP servers, JSON encoding, templating, cryptography, and concurrency primitives all ship with the language. A weekend project can go a long way before it needs a third-party dependency.

**Deployment is a single binary.** Cross-compile, copy the binary to a server, and run it. When the demo has to work by Sunday night, fewer moving parts means fewer surprises.

**Interfaces divide the work cleanly.** Teams can agree on a small interface early. Then one person builds the storage layer while another builds the HTTP handlers, and neither has to wait for the other.

## Why we're taking part

We run Go in production for several of our backend services, and it has earned its place there. A hackathon tests different skills than production work does, though. You have to make fast decisions, cut scope without mercy, and ship something with a clear purpose by a fixed deadline.

Our engineers will also try parts of the language and ecosystem they don't use day to day. A team that normally works on internal APIs may build a terminal tool or a small game. That kind of exploration often leads to ideas we bring back to our main work.

And it's fun. Building something with the global Go community, all at the same time, is a good reason to spend a weekend writing code.

## Tips for a 48-hour project

Here's what we've learned from past internal hack weeks:

1. **Scope down, then scope down again.** Whatever you plan to build, a smaller version will probably come out better. A polished small tool beats an ambitious prototype that doesn't run.
2. **Write the README first.** If you can't explain the project in a paragraph, you aren't ready to code. The README also becomes your pitch to the judges.
3. **Define interfaces early.** Spend the first hour agreeing on the main types and function signatures. It pays off for the rest of the weekend.
4. **Use the standard library as long as you can.** Every dependency adds risk. Reach for `net/http` and `encoding/json` before you pull in a framework.
5. **Commit often.** Small commits make collaboration easier and show the judges how the project grew.
6. **Sleep.** Code written after 30 hours awake often has to be rewritten. A rested team ships better work than an exhausted one.

## Join in

If you write Go, or want an excuse to learn it, the Gopher Gala is a low-pressure way to build something real with other gophers. Find a few collaborators, or sign up alone, and pick an idea that excites you.

We'll share what our teams built after the event, including what worked, what didn't, and what we'd do differently. See you on the leaderboard.
