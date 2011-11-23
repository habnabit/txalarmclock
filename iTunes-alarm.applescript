#!/usr/bin/osascript
--*- coding: mac-roman -*-

on run argv
  set minVolume to item 1 of argv as integer
  set maxVolume to item 2 of argv as integer
  set interval to item 3 of argv as real
  set snooze to item 4 of argv as real
  set snoozeRestoreVolume to item 5 of argv as integer
  set selectionPlaylist to item 6 of argv

  set delayInterval to interval / (maxVolume - minVolume)
  tell application "iTunes"
    set sound volume to minVolume
    set ourTrack to some item of playlist selectionPlaylist's tracks
    play ourTrack with once
    repeat until player state is stopped
      if sound volume < maxVolume and player state is playing then set sound volume to sound volume + 1
      if player state is paused and snooze ≠ 0 then
        delay snooze
        set sound volume to snoozeRestoreVolume
        play ourTrack with once
      end if
      delay delayInterval
    end repeat
  end tell
end run
