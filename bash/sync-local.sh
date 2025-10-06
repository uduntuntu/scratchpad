#!/bin/bash
for f in $(ls);
do
	[ "$f" = "sync-local.sh" ] && continue
	ln -svfnT $(pwd)/$f ~/.local/bin/$f
done
