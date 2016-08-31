/**
 * Module which initializes the desktop user's javascript environment.
 * It is effectively the `main` module.
 */
$(document).ready(function(){ // container for entire script
    
    var API_BASE_PATH = '/api/v1/';
    var BASE_DOMAIN = 'http://gravvy.nnoduka.com';
    
    /**
     * Get any given cookie, using code from django docs
     * @ref https://docs.djangoproject.com/en/dev/ref/csrf/#ajax
     *
     * @param name  Name of cookie of interest
     */
    function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(
                    name.length + 1));
                break;
            }
        }
    }
        return cookieValue;
    }
    
    /**
     * Set the header on your AJAX request, while protecting the CSRF token 
     * from being sent to other domains using settings.crossDomain
     */
    var csrftoken = getCookie('csrftoken');
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    
    /**
     * Return a number is formatted with commas
     *
     * @param num integer to be formatted
     *
     * @return string representation of integer
     *
     * @ref http://stackoverflow.com/a/2901298
     */
    function numberWithCommas(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
    
    /* Open popup window with a given location url. 
     * Useful for sharing content on social media
     *
     * @param location URL to open in popup.
     * @return None
     */
    function openPopupWindow (location) {
        window.open(location, "_blank",
                     "status=1,toolbar=0, location=0, menubar=0,directories=0,resizeable=0, width=700, height=350");
    }
    
    /* Share a url on Facebook with a given title.
     *
     * @param url URL to share
     * @param title title to use when sharing
     *
     * @return None
     */
    function facebookShare(url, title) {
        var location = "https://www.facebook.com/sharer.php?u="+
            encodeURIComponent(url) + "&t" + encodeURIComponent(title);
        openPopupWindow(location);
    }

    /* Share a url on Twitter with a given title.
     *
     * @param url URL to share
     * @param title title to use when sharing
     *
     * @return None
     */
    function twitterShare(url, title) {
        var location = "http://twitter.com/share?text="+
            encodeURIComponent("#np "+ title.substring(0,90)) +
            "&via=gravyapp&url=" + encodeURIComponent(url);
        openPopupWindow(location);
    }
    
    // Install flowplayer into video element
    if ($("#player").length > 0) {
                
        /**
         * Record a play of the current video
         */
        function playedVideo() {
            var hashkey = $("#player").data('hashkey');
            var url = API_BASE_PATH + 'videos/' + hashkey + '/play/';
            $.ajax({
                type:'PUT',
                url:url,
                success:function(data) {
                    $("p#plays-count span").text(
                        numberWithCommas(data['plays_count']));
                },
                error: function(data) {
                },
                dataType:'json',
                cache:false // ensures forward/back buttons work properly
            });
        }
        
        // Install flowplayer
        $("#player").flowplayer({
            swf:'//gravvy-static.s3.amazonaws.com/flowplayer/flowplayer.swf',
            
            // clip properties common to all playlist entries
            autoplay:true,
            loop:true,
            ratio:1/1,
            volume: 1.0,
            embed: false,
            fullscreen: true,
            // our playlist 
            playlist: all_clips
        });
        
        // We don't get the initial clip index 0 load event so execute
        // callback on page load
        playedVideo();
        
        // Have we forced playlist to start at the right clip?
        var playlistIndexUsed = false;

        flowplayer(0).on("load", function(e, api, video) {
            // current clip index is at `video.index`
            // indicator of if this is last clip in playlist is `video.is_last`
            if (video.index == 0) {playedVideo()};
                        
        }).on("cuepoint", function(e, api, cuepoint) {
            // video is accessible at `api.video`
            // current clip index is `api.video.index`
            // cuepoint time is at `cuepoint.time`
            
        }).on("ready", function(e, api, video) {
            if (!playlistIndexUsed) {
                if (playlistStartIndex > 0 && 
                    playlistStartIndex < all_clips.length) {
                    api.play(playlistStartIndex);
                }
                playlistIndexUsed = true;
            }
        });
        
        // Did we pause player on blur ?
        var pausedOnBlur = false;
        // Pause player on window disappearance if playing and renable on
        // window appearance
        $(window).blur(function() {
            // player currently playing, so pause on window blur
            if ((flowplayer(0).playing == true) && 
                (flowplayer(0).loading == false)) {
                pausedOnBlur = true;
                flowplayer(0).pause();
            } else {
                pausedOnBlur = false;
            }
        }).focus(function() {
            // player paused and done on window blur, so resume player on focus
            if ((flowplayer(0).paused == true) && (pausedOnBlur == true)) {
                flowplayer(0).resume();
            }
            // reset the pause boolean
            pausedOnBlur = false;
        });
        
        
        // Setup timestamp
        var timestamp = $("#video-timestamp").data('timestamp');
        var formatted_timestamp = moment(timestamp).format('MMM D, YYYY');
        $("#video-timestamp").text(formatted_timestamp);
        
        // Setup social media sharing
        var hashkey = $("#player").data('hashkey');
        var video_details_url = BASE_DOMAIN + '/v/'+ hashkey + '/'; 
        var video_title = $("#player").data('title');
        var share_title = "Gravvy App Video";
        if (video_title.length > 0) {
            share_title = share_title +": "+video_title;
        }
        $("#social-share .twitter").click(function() {
            twitterShare(
                video_details_url, share_title);
        });
        $("#social-share .facebook").click(function() {
            facebookShare(
                video_details_url, share_title);
        });
        
    } // End player logic
    
    // Logic for phone number input elements
    if ($("#id_number").length > 0) {
        $("#id_number").intlTelInput({
            defaultCountry: "auto",
            geoIpLookup: function(callback) {
                $.get('http://ipinfo.io', function() {}, "jsonp").always(
                    function(resp) {
                        var countryCode = (resp && resp.country) ? 
                                          resp.country : "";
                        callback(countryCode);
                    });
            },
            preferredCountries: ["ng", "us", "gb"],
            utilsScript: libPhoneNumberUtilsScript
        });
        
        // Catch the submit event and perform validation
        $("#formUpload").submit(function(event) {
            if ($("#id_number").intlTelInput("isValidNumber")) {
                // Set E.164 formatted phone number
                $("#id_formatted_number").val(
                    $("#id_number").intlTelInput("getNumber"));
                
            } else {
                // prevent default, we will be showing error messages
                event.preventDefault();
                
                var errorMessage = "This is an invalid number";
                var error = $("#id_number").intlTelInput(
                    "getValidationError");
                if (error == intlTelInputUtils.validationError.TOO_SHORT) {
                    errorMessage = "This number is too short to be valid";
                
                } else if (error == 
                    intlTelInputUtils.validationError.TOO_LONG) {
                    errorMessage = "This number is too long to be valid";
                    
                } else if (error == 
                    intlTelInputUtils.validationError.NOT_A_NUMBER) {
                    errorMessage = "This is not a number";
                }
                
                var errorList = $("#number_errorlist");
                errorList.empty();
                errorList.append($('<li/>', {text: errorMessage}));
            }
        });
        
    } // End phone number input element
    
    
    // Initialize the Popover data-apis
    $(function () {
        $('[data-toggle="popover"]').popover()
    });
    
    // Deal with window resize not repositioning popover
    $(window).resize(function() {
        $(".popover:visible").popover('show');
    });
    
}); // end container for entire script
