#!/usr/bin/osascript
set minVolume to 15
set maxVolume to 40
set interval to 30
set snooze to 5
set snoozeRestoreVolume to 20
set selectionPlaylist to "Things to Wake Up Three"

set delayInterval to interval / (maxVolume - minVolume)
tell application "iTunes"
    set sound volume to minVolume
    set ourTrack to some item of playlist selectionPlaylist's tracks
    play ourTrack with once
    repeat until player state is stopped
        if sound volume < maxVolume and player state is playing then set sound volume to sound volume + 1
        if player state is paused and snooze ­ 0 then
            delay snooze
            set sound volume to snoozeRestoreVolume
            play ourTrack with once
        end if
        delay delayInterval
    end repeat
end tell
