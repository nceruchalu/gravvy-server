#!/bin/bash
# This script processes a video file to simulate what the native app would do:
#     - Generate a photo snapshot of the first frame
#     - Trim the video file to be no longer than 6 seconds, then resizes and
#       crops it to 480x480
#
# Positional Args:
#     - Input video name
#     - Output video name
#     - Output image name
#     - Output video duration name
#     - Location of ffmpeg binary. Use blank string if the system default works
#
# Refs:
#     - Trimming video: http://superuser.com/a/141343
#     - Resizing video: http://unix.stackexchange.com/a/192021

# Grab the input and output files from the positional arguments
FILE="$1"
OUT="$2"
OUT_IMAGE="$3"
OUT_DURATION="$4"
FFMPEG_PATH="$5"

# Trimmed and resized videos with random numbers appended to them, so there
# aren't conflicts if multiple shell processes are running
TRIMMED="/tmp/trimmed$$.mp4"
RESIZED="/tmp/resized$$.mp4"

LOGLEVEL="panic"

OUT_WIDTH=480
OUT_HEIGHT=480

TRIM_DURATION=6

# trim the input video to be no longer than TRIM_DURATION
${FFMPEG_PATH}ffmpeg -loglevel ${LOGLEVEL} -i ${FILE} -y -ss 0 -c copy -t ${TRIM_DURATION} ${TRIMMED}

# Determine if the video is rotated
ROTATION=`${FFMPEG_PATH}ffprobe -show_streams ${TRIMMED}  2>/dev/null  | grep rotate | sed -n 's/TAG:rotate=//p'`

# Generate the output image
${FFMPEG_PATH}ffmpeg -loglevel ${LOGLEVEL} -i ${FILE} -y -vframes 1 -f image2 ${OUT_IMAGE}

# Get the size of input video:
eval $(${FFMPEG_PATH}ffprobe -v error -of flat=s=_ -select_streams v:0 -show_entries stream=height,width ${TRIMMED})
IN_WIDTH=${streams_stream_0_width}
IN_HEIGHT=${streams_stream_0_height}

# Let's take the shorter side, so the video will be at least as big
# as the desired size:
CROP_SIDE="n"

# is the height shorter?
if [ "${ROTATION}" == "90" ] || [ "${ROTATION}" == "270" ] ; then
    if [ ${IN_WIDTH} -lt ${IN_HEIGHT} ] ; then
        SCALE="-2:${OUT_HEIGHT}"
        CROP_SIDE="w"
    else
        SCALE="${OUT_WIDTH}:-2"
        CROP_SIDE="h"
    fi
else
    # Not rotated so do proper checks
    if [ ${IN_HEIGHT} -lt ${IN_WIDTH} ] ; then
        SCALE="-2:${OUT_HEIGHT}"
        CROP_SIDE="w"
    else
        SCALE="${OUT_WIDTH}:-2"
        CROP_SIDE="h"
    fi
fi

# Then perform a first resizing
${FFMPEG_PATH}ffmpeg -loglevel ${LOGLEVEL} -i ${TRIMMED} -strict -2 -y -vf scale=${SCALE} ${RESIZED}

# Now get the temporarily resized video size
eval $(${FFMPEG_PATH}ffprobe -v error -of flat=s=_ -select_streams v:0 -show_entries stream=height,width ${RESIZED})
IN_WIDTH=${streams_stream_0_width}
IN_HEIGHT=${streams_stream_0_height}

# Calculate how much we should crop
if [ "z${CROP_SIDE}" = "zh" ] ; then
  DIFF=$[ ${IN_HEIGHT} - ${OUT_HEIGHT} ]
  CROP="in_w:in_h-${DIFF}"
elif [ "z${CROP_SIDE}" = "zw" ] ; then
  DIFF=$[ ${IN_WIDTH} - ${OUT_WIDTH} ]
  CROP="in_w-${DIFF}:in_h"
fi

# Then crop...
${FFMPEG_PATH}ffmpeg -loglevel ${LOGLEVEL} -i ${RESIZED} -strict -2 -y -filter:v "crop=${CROP}" ${OUT}

# Cleanup files. Redirect errors because this generates some if the script 
# ran into some ttrouble and never created these files
rm $TRIMMED $RESIZED 2> /dev/null

# Finally determine length of output file
${FFMPEG_PATH}ffprobe -i ${OUT} -show_format -v quiet | sed -n 's/duration=//p' > ${OUT_DURATION}
