#!/bin/sh
set -e
cat > go.mod <<'X'
module example.com/worker

go 1.23
X
cat > worker.go <<'X'
package worker

import (
	"sync"
	"time"
)

// Process runs handle on every item concurrently and returns the errors.
func Process(items []string, handle func(string) error) []error {
	var wg sync.WaitGroup
	errs := make([]error, 0)
	for _, it := range items {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if err := handle(it); err != nil {
				errs = append(errs, err)
			}
		}()
	}
	wg.Wait()
	return errs
}

// Poll calls tick once a second until stop is closed.
func Poll(stop <-chan struct{}, tick func()) {
	for {
		select {
		case <-stop:
			return
		case <-time.After(time.Second):
			tick()
		}
	}
}
X
