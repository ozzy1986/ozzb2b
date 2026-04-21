jQuery(window).on('load', function() {
  jQuery('.prev-photo i').show();
  jQuery('.next-photo i').show();  
});

jQuery(document).ready(function() {

  //BXSlider chrome event click fix
  if(window.navigator.userAgent.toLowerCase().indexOf("chrome") > 0) {
      jQuery("body").on("mousedown", ".bx-viewport a", function() { 
          if(jQuery(this).attr("href") && jQuery(this).attr("href") != "#") {
              window.location=jQuery(this).attr("href"); 
          } 
      }); 
  }

  /** PHOTOS GALLERY */
  jQuery(".wp-block-gallery a").attr('data-fancybox', 'gallery');
  if( jQuery('.wp-block-gallery').length > 0 ){
    // var imgs = document.images,
    var imgs = jQuery('.wp-block-gallery img'),
    len = imgs.length,
    counter = 0;
    [].forEach.call( imgs, function( img ) {
        if(img.complete){
          incrementCounter();
        }else{
          img.addEventListener( 'load', incrementCounter, false );
        }
    } );
    function incrementCounter() {
        counter++;
        jQuery('.loading-photos span').text(counter + '/' + len);
        if ( counter === len ) {
          waterfall('.wp-block-gallery');
              setTimeout(function(){
                jQuery('.wp-block-gallery').css('opacity', 1);
                jQuery('.loading-photos').hide();
              }, 1000);
        }
    }
    jQuery( window ).resize(function() {
      waterfall('.wp-block-gallery');
    });
    jQuery( window ).load(function() {
      waterfall('.wp-block-gallery');
    });
  }
  jQuery(".gallery a").attr('data-fancybox', 'gallery');
  if( jQuery('.gallery').length > 0 ){
    // var imgs = document.images,
    var imgs = jQuery('.gallery img'),
    len = imgs.length,
    counter = 0;
    [].forEach.call( imgs, function( img ) {
        if(img.complete){
          incrementCounter();
        }else{
          img.addEventListener( 'load', incrementCounter, false );
        }
    } );
    function incrementCounter() {
        counter++;
        jQuery('.loading-photos span').text(counter + '/' + len);
        if ( counter === len ) {
          waterfall('.gallery');
              setTimeout(function(){
                jQuery('.gallery').css('opacity', 1);
                jQuery('.loading-photos').hide();
              }, 1000);
        }
    }
    jQuery( window ).resize(function() {
      waterfall('.gallery');
    });
  }

  /** VideoJS loading **/
  if(jQuery('#wpst-video').length > 0 && !wpst_ajax_var.ctpl_installed){
      var playerOptions = {
        controlBar: {
          children: [
                'playToggle',           
                'progressControl', 
                'durationDisplay',
                'volumePanel',
                'qualitySelector',
                'fullscreenToggle',
          ],
        },
      };
      videojs('wpst-video', playerOptions);
  }
    
  /** Lazy load **/
  var imgDefer = document.getElementsByTagName('img');
  for (var i=0; i<imgDefer.length; i++){
      var dataSrc = imgDefer[i].getAttribute('data-src');
      if( dataSrc ) {
          imgDefer[i].setAttribute( 'src', dataSrc );
          imgDefer[i].classList.add('display-img');
      }
  }

  /** Tabs **/
  jQuery('.tab-link').on('click', function(e)  {
      var tabId = jQuery(this).data('tab-id');
      // Show/Hide Tabs
      jQuery('#' + tabId).show().siblings().hide();
      // Change/remove current tab to active
      jQuery(this).addClass('active').siblings().removeClass('active');
      e.preventDefault();
  });

  /** In-video Ad Close button **/    
  // if(wpst_ajax_var.ctpl_installed == ''){
    jQuery('body').on('click', '.happy-inside-player .close', function(e) {
      jQuery(this).parent('.happy-inside-player').hide();
    });
  // }

  /** IIFE Set Post views with ajax request for cache compatibility */
  (function(){
    var is_post = jQuery('body.single-post').length > 0;
    if( !is_post ) return;
    var post_id = jQuery('article.post').attr('id').replace('post-', '');
    jQuery.ajax({
      type: 'post',
      url: wpst_ajax_var.url,
      dataType: 'json',
      data: {
        action: 'post-views',
        nonce: wpst_ajax_var.nonce,
        post_id: post_id
      }          
    })
    .done(function(doneData){
      // console.log(doneData);
    })
    .fail(function(errorData){
      console.error(errorData);
    })
    .always(function(alwaysData){
      //get post views & rating data
      jQuery.ajax({
        type: 'post',
        url: wpst_ajax_var.url,
        dataType: 'json',
        data: {
          action: 'get-post-data',
          nonce: wpst_ajax_var.nonce,
          post_id: post_id
        }
      })
      .done(function(doneData){
        if(doneData.views) {
          jQuery("#video-views span").text(doneData.views);
        }
        if(doneData.likes) {
            jQuery(".likes_count").text(doneData.likes);
        }
        if(doneData.dislikes) {
            jQuery(".dislikes_count").text(doneData.dislikes);
        }
        if(doneData.rating) {
            jQuery(".percentage").text(doneData.rating);
            jQuery(".rating-bar-meter").css('width', doneData.rating);
        }
      })
      .fail(function(errorData){
        console.error(errorData);
      })
      .always(function(){
        // always stuff
      })
    });
  })();

    /** Post like **/
    jQuery(".post-like a").on('click', function(e){
        e.preventDefault();

        var heart = jQuery(this);
        var post_id = heart.data("post_id");
        var post_like = heart.data("post_like");

        jQuery.ajax({
            type: "post",
            url: wpst_ajax_var.url,
            dataType   : "json",
            data: "action=post-like&nonce=" + wpst_ajax_var.nonce + "&post_like=" + post_like + "&post_id=" + post_id,
            success    : function(data, textStatus, jqXHR){
                if(data.alreadyrate !== true) {
                    jQuery(".rating-bar-meter").removeClass("not-rated-yet");
                    /*jQuery(".rating").text(Math.floor(data.pourcentage) + "%");
                    jQuery(".rating").show();*/

                    jQuery(".rating-result .percentage").text(Math.floor(data.percentage) + "%");
                    jQuery(".rating-result .percentage").show();

                    jQuery(".likes .likes_count").text(data.likes);
                    jQuery(".likes .dislikes_count").text(data.dislikes);

                    jQuery(".post-like").text(data.button);

                    if( data.nbrates > 0 ){
                        jQuery(".rating-bar-meter").animate({
                            width: data.progressbar + "%",
                        }, "fast", function() {
    // Animation complete.
    });
                    }
                }
            }
        });
        return false;
    });    

    //Main thumbs
    main_setThumbsHeight();

    function ratio_format(){
      var width = options.thumbnails_ratio.split('/')[0];
      var height = options.thumbnails_ratio.split('/')[1];
      return height / width;
    }

    jQuery( window ).resize(function() {        
        main_setThumbsHeight();
    });
    function main_setThumbsHeight(){
        var eltWidthMain = jQuery(jQuery('.post-thumbnail')[0]).width();
        jQuery('.post-thumbnail img').height( eltWidthMain * ratio_format() );
        jQuery('.post-thumbnail .wpst-trailer').height( eltWidthMain * ratio_format() );
        jQuery('.photos .post-thumbnail .photo-bg').height( eltWidthMain );
        jQuery('.post-thumbnail .no-thumb').height( eltWidthMain * ratio_format() );
    }    

    //Sidebar thumbs
    sidebar_setThumbsHeight();

    jQuery( window ).resize(function() {
        sidebar_setThumbsHeight();
    });
    function sidebar_setThumbsHeight(){
        var eltWidthSidebar = jQuery(jQuery('#sidebar .post-thumbnail')[0]).width();
        jQuery('#sidebar .post-thumbnail img').height( eltWidthSidebar * ratio_format() );
        jQuery('#sidebar .post-thumbnail .wpst-trailer').height( eltWidthSidebar * ratio_format() );
        jQuery('#sidebar .no-thumb').height( eltWidthSidebar * ratio_format() );
    }

    //Footer thumbs
    footer_setThumbsHeight();

    jQuery( window ).resize(function() {
        footer_setThumbsHeight();
    });
    function footer_setThumbsHeight(){
        var eltWidthFooter = jQuery(jQuery('.site-footer .post-thumbnail')[0]).width();
        jQuery('.site-footer .post-thumbnail img').height( eltWidthFooter * ratio_format() );
        jQuery('.site-footer .post-thumbnail .wpst-trailer').height( eltWidthFooter * ratio_format() );
        jQuery('.site-footer .no-thumb').height( eltWidthFooter * ratio_format() );
    }

    //Hide title hover thumb
    jQuery('.thumb-block a').hover(function(e){
      jQuery(this).attr('data-title', jQuery(this).attr('title'));
      jQuery(this).removeAttr('title');
    },
    function(e){
        jQuery(this).attr('title', jQuery(this).attr('data-title'));
    });

    //Trailer
    jQuery('.video-with-trailer').each(function(i, obj) {
        jQuery(this).on("mouseover", function() { hoverVideo(i); });        
        jQuery(this).on("mouseout", function() { hideVideo(i); });
    });

    //Multithumbs
    var changeThumb = null;
    var stopped = false;
    jQuery('body').on('mouseenter', '.thumbs-rotation', function(e){
        var $this = jQuery(this);
        stopped = false;
        if( $this.data('thumbs') != undefined ){
            var dataThumbs = $this.data('thumbs');
            var thumbs = dataThumbs.split(',');
            var nbThumbs = thumbs.length;
            var i = 1;
            changeThumb = null;
            clearTimeout(changeThumb);
            changeThumb = function() {
                if( stopped == false ){
                    $this.find('img').attr('srcset', thumbs[i - 1]);
                    if (i <= nbThumbs ) {
                        setTimeout(changeThumb, 700);
                        if( i == nbThumbs){
                            i = 1;
                        }else{
                          i++;
                        }
                    }
                }
            };
            changeThumb();
        }
    }).on('mouseleave', '.thumbs-rotation', function(e){
        stopped = true;
        changeThumb = null;
        var highestTimeoutId = setTimeout(";");
        for (var i = 0 ; i < highestTimeoutId ; i++) {
            clearTimeout(i);
        }
        var $blockImg = jQuery(this).find('img');
        var defaultThumb = $blockImg.attr('src');
        $blockImg.attr('srcset', defaultThumb);
    });

    jQuery('.video-description .more').readmore({
      speed: 75,
      collapsedHeight: 50,
      moreLink: '<a class="morelink" href="#">' + objectL10nMain.readmore + ' <i class="fa fa-chevron-down"></i></a>',
      lessLink: '<a class="morelink" href="#">' + objectL10nMain.close + ' <i class="fa fa-chevron-up"></i></a>'
    });

    /** Back to top */
    if (jQuery('#back-to-top').length) {
        var scrollTrigger = 100, // px
            backToTop = function () {
                var scrollTop = jQuery(window).scrollTop();
                if (scrollTop > scrollTrigger) {
                    jQuery('#back-to-top').addClass('show');
                } else {
                    jQuery('#back-to-top').removeClass('show');
                }
            };
        backToTop();
        jQuery(window).on('scroll', function () {
            backToTop();
        });
        jQuery('#back-to-top').on('click', function (e) {
            e.preventDefault();
            jQuery('html,body').animate({
                scrollTop: 0
            }, 300);
        });
    }

});


/** TRAILER */
function hoverVideo(i) {
  var playPromise = jQuery('.wpst-trailer')[i].play();
  if (playPromise !== undefined) {
      playPromise.then(_ => {
  // Automatic playback started!
  // Show playing UI.
  })
  .catch(error => {
  // Auto-play was prevented
  // Show paused UI.
  });
  }
}

function hideVideo(i) {
  //jQuery('.wpst-trailer')[i].currentTime = 0; 
  jQuery('.wpst-trailer')[i].load(); 
}

/** LOGIN / REGISTER POPUP */
function wpst_open_login_dialog(href){
    
    jQuery('#wpst-user-modal .modal-dialog').removeClass('registration-complete');

    var modal_dialog = jQuery('#wpst-user-modal .modal-dialog');
    modal_dialog.attr('data-active-tab', '');

    switch(href){

        case '#wpst-register':
            modal_dialog.attr('data-active-tab', '#wpst-register');
            break;

        case '#wpst-login':
        default:
            modal_dialog.attr('data-active-tab', '#wpst-login');
            break;
    }

    jQuery('#wpst-user-modal').modal('show');
}	

function wpst_close_login_dialog(){

    jQuery('#wpst-user-modal').modal('hide');
}	

jQuery(function($){

    "use strict";
    /***************************
    **  LOGIN / REGISTER DIALOG
    ***************************/

    // Open login/register modal
    $('[href="#wpst-login"], [href="#wpst-register"]').click(function(e){

        e.preventDefault();

        wpst_open_login_dialog( $(this).attr('href') );

    });

    // Switch forms login/register
    $('.modal-footer a, a[href="#wpst-reset-password"]').click(function(e){
        e.preventDefault();
        $('#wpst-user-modal .modal-dialog').attr('data-active-tab', $(this).attr('href'));
    });
    
    // Post login form
    $('#wpst_login_form').on('submit', function(e){

        e.preventDefault();

        var button = $(this).find('button');
            button.button('loading'); 

        $.post(wpst_ajax_var.url, $('#wpst_login_form').serialize(), function(data){

            var obj = $.parseJSON(data);

            $('.wpst-login .wpst-errors').html(obj.message);
            
            if(obj.error == false){
                $('#wpst-user-modal .modal-dialog').addClass('loading');
                window.location.reload(true);
                button.hide();
            }

            button.button('reset');
        });

    });


    // Post register form
    $('#wpst_registration_form').on('submit', function(e){

        e.preventDefault();

        var button = $(this).find('button');
            button.button('loading');

        $.post(wpst_ajax_var.url, $('#wpst_registration_form').serialize(), function(data){
            
            var obj = $.parseJSON(data);

            $('.wpst-register .wpst-errors').html(obj.message);
            
            if(obj.error == false){
                $('#wpst-user-modal .modal-dialog').addClass('registration-complete');
                // window.location.reload(true);
                button.hide();
            }

            button.button('reset');
            
        });

    });


    // Reset Password
    $('#wpst_reset_password_form').on('submit', function(e){

        e.preventDefault();

        var button = $(this).find('button');
            button.button('loading');

        $.post(wpst_ajax_var.url, $('#wpst_reset_password_form').serialize(), function(data){

            var obj = $.parseJSON(data);

            $('.wpst-reset-password .wpst-errors').html(obj.message);
            
            // if(obj.error == false){
                // $('#wpst-user-modal .modal-dialog').addClass('loading');
                // $('#wpst-user-modal').modal('hide');
            // }

            button.button('reset');
        });

    });

    if(window.location.hash == '#login'){
        wpst_open_login_dialog('#wpst-login');
    }		

});

/*!
* @preserve
*
* Readmore.js jQuery plugin
* Author: @jed_foster
* Project home: http://jedfoster.github.io/Readmore.js
* Licensed under the MIT license
*
* Debounce function from http://davidwalsh.name/javascript-debounce-function
*/

/* global jQuery */

(function(factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD
    define(['jquery'], factory);
  } else if (typeof exports === 'object') {
    // CommonJS
    module.exports = factory(require('jquery'));
  } else {
    // Browser globals
    factory(jQuery);
  }
  }(function($) {
  'use strict';
  
  var readmore = 'readmore',
      defaults = {
        speed: 100,
        collapsedHeight: 200,
        heightMargin: 16,
        moreLink: '<a href="#">Read More</a>',
        lessLink: '<a href="#">Close</a>',
        embedCSS: true,
        blockCSS: 'display: block; width: 100%;',
        startOpen: false,
  
        // callbacks
        blockProcessed: function() {},
        beforeToggle: function() {},
        afterToggle: function() {}
      },
      cssEmbedded = {},
      uniqueIdCounter = 0;
  
  function debounce(func, wait, immediate) {
    var timeout;
  
    return function() {
      var context = this, args = arguments;
      var later = function() {
        timeout = null;
        if (! immediate) {
          func.apply(context, args);
        }
      };
      var callNow = immediate && !timeout;
  
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
  
      if (callNow) {
        func.apply(context, args);
      }
    };
  }
  
  function uniqueId(prefix) {
    var id = ++uniqueIdCounter;
  
    return String(prefix == null ? 'rmjs-' : prefix) + id;
  }
  
  function setBoxHeights(element) {
    var el = element.clone().css({
          height: 'auto',
          width: element.width(),
          maxHeight: 'none',
          overflow: 'hidden'
        }).insertAfter(element),
        expandedHeight = el.outerHeight(),
        cssMaxHeight = parseInt(el.css({maxHeight: ''}).css('max-height').replace(/[^-\d\.]/g, ''), 10),
        defaultHeight = element.data('defaultHeight');
  
    el.remove();
  
    var collapsedHeight = cssMaxHeight || element.data('collapsedHeight') || defaultHeight;
  
    // Store our measurements.
    element.data({
      expandedHeight: expandedHeight,
      maxHeight: cssMaxHeight,
      collapsedHeight: collapsedHeight
    })
    // and disable any `max-height` property set in CSS
    .css({
      maxHeight: 'none'
    });
  }
  
  var resizeBoxes = debounce(function() {
    $('[data-readmore]').each(function() {
      var current = $(this),
          isExpanded = (current.attr('aria-expanded') === 'true');
  
      setBoxHeights(current);
  
      current.css({
        height: current.data( (isExpanded ? 'expandedHeight' : 'collapsedHeight') )
      });
    });
  }, 100);
  
  function embedCSS(options) {
    if (! cssEmbedded[options.selector]) {
      var styles = ' ';
  
      if (options.embedCSS && options.blockCSS !== '') {
        styles += options.selector + ' + [data-readmore-toggle], ' +
          options.selector + '[data-readmore]{' +
            options.blockCSS +
          '}';
      }
  
      // Include the transition CSS even if embedCSS is false
      styles += options.selector + '[data-readmore]{' +
        'transition: height ' + options.speed + 'ms;' +
        'overflow: hidden;' +
      '}';
  
      (function(d, u) {
        var css = d.createElement('style');
        css.type = 'text/css';
  
        if (css.styleSheet) {
          css.styleSheet.cssText = u;
        }
        else {
          css.appendChild(d.createTextNode(u));
        }
  
        d.getElementsByTagName('head')[0].appendChild(css);
      }(document, styles));
  
      cssEmbedded[options.selector] = true;
    }
  }
  
  function Readmore(element, options) {
    this.element = element;
  
    this.options = $.extend({}, defaults, options);
  
    embedCSS(this.options);
  
    this._defaults = defaults;
    this._name = readmore;
  
    this.init();
  
    // IE8 chokes on `window.addEventListener`, so need to test for support.
    if (window.addEventListener) {
      // Need to resize boxes when the page has fully loaded.
      window.addEventListener('load', resizeBoxes);
      window.addEventListener('resize', resizeBoxes);
    }
    else {
      window.attachEvent('load', resizeBoxes);
      window.attachEvent('resize', resizeBoxes);
    }
  }
  
  
  Readmore.prototype = {
    init: function() {
      var current = $(this.element);
  
      current.data({
        defaultHeight: this.options.collapsedHeight,
        heightMargin: this.options.heightMargin
      });
  
      setBoxHeights(current);
  
      var collapsedHeight = current.data('collapsedHeight'),
          heightMargin = current.data('heightMargin');
  
      if (current.outerHeight(true) <= collapsedHeight + heightMargin) {
        // The block is shorter than the limit, so there's no need to truncate it.
        if (this.options.blockProcessed && typeof this.options.blockProcessed === 'function') {
          this.options.blockProcessed(current, false);
        }
        return true;
      }
      else {
        var id = current.attr('id') || uniqueId(),
            useLink = this.options.startOpen ? this.options.lessLink : this.options.moreLink;
  
        current.attr({
          'data-readmore': '',
          'aria-expanded': this.options.startOpen,
          'id': id
        });
  
        current.after($(useLink)
          .on('click', (function(_this) {
            return function(event) {
              _this.toggle(this, current[0], event);
            };
          })(this))
          .attr({
            'data-readmore-toggle': id,
            'aria-controls': id
          }));
  
        if (! this.options.startOpen) {
          current.css({
            height: collapsedHeight
          });
        }
  
        if (this.options.blockProcessed && typeof this.options.blockProcessed === 'function') {
          this.options.blockProcessed(current, true);
        }
      }
    },
  
    toggle: function(trigger, element, event) {
      if (event) {
        event.preventDefault();
      }
  
      if (! trigger) {
        trigger = $('[aria-controls="' + this.element.id + '"]')[0];
      }
  
      if (! element) {
        element = this.element;
      }
  
      var $element = $(element),
          newHeight = '',
          newLink = '',
          expanded = false,
          collapsedHeight = $element.data('collapsedHeight');
  
      if ($element.height() <= collapsedHeight) {
        newHeight = $element.data('expandedHeight') + 'px';
        newLink = 'lessLink';
        expanded = true;
      }
      else {
        newHeight = collapsedHeight;
        newLink = 'moreLink';
      }
  
      // Fire beforeToggle callback
      // Since we determined the new "expanded" state above we're now out of sync
      // with our true current state, so we need to flip the value of `expanded`
      if (this.options.beforeToggle && typeof this.options.beforeToggle === 'function') {
        this.options.beforeToggle(trigger, $element, ! expanded);
      }
  
      $element.css({'height': newHeight});
  
      // Fire afterToggle callback
      $element.on('transitionend', (function(_this) {
        return function() {
          if (_this.options.afterToggle && typeof _this.options.afterToggle === 'function') {
            _this.options.afterToggle(trigger, $element, expanded);
          }
  
          $(this).attr({
            'aria-expanded': expanded
          }).off('transitionend');
        }
      })(this));
  
      $(trigger).replaceWith($(this.options[newLink])
        .on('click', (function(_this) {
            return function(event) {
              _this.toggle(this, element, event);
            };
          })(this))
        .attr({
          'data-readmore-toggle': $element.attr('id'),
          'aria-controls': $element.attr('id')
        }));
    },
  
    destroy: function() {
      $(this.element).each(function() {
        var current = $(this);
  
        current.attr({
          'data-readmore': null,
          'aria-expanded': null
        })
          .css({
            maxHeight: '',
            height: ''
          })
          .next('[data-readmore-toggle]')
          .remove();
  
        current.removeData();
      });
    }
  };
  
  
  $.fn.readmore = function(options) {
    var args = arguments,
        selector = this.selector;
  
    options = options || {};
  
    if (typeof options === 'object') {
      return this.each(function() {
        if ($.data(this, 'plugin_' + readmore)) {
          var instance = $.data(this, 'plugin_' + readmore);
          instance.destroy.apply(instance);
        }
  
        options.selector = selector;
  
        $.data(this, 'plugin_' + readmore, new Readmore(this, options));
      });
    }
    else if (typeof options === 'string' && options[0] !== '_' && options !== 'init') {
      return this.each(function () {
        var instance = $.data(this, 'plugin_' + readmore);
        if (instance instanceof Readmore && typeof instance[options] === 'function') {
          instance[options].apply(instance, Array.prototype.slice.call(args, 1));
        }
      });
    }
  };
  
  }));

/********************/
/** Bootstrap modal */
/********************/
/*!
 * Bootstrap v3.3.7 (http://getbootstrap.com)
 * Copyright 2011-2017 Twitter, Inc.
 * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
 */

/*!
 * Generated using the Bootstrap Customizer (http://getbootstrap.com/docs/3.3/customize/?id=2df80e69d208c504c2a17d0146de73bb)
 * Config saved to config.json and https://gist.github.com/2df80e69d208c504c2a17d0146de73bb
 */
if (typeof jQuery === 'undefined') {
    throw new Error('Bootstrap\'s JavaScript requires jQuery')
  }
  +function ($) {
    'use strict';
    var version = $.fn.jquery.split(' ')[0].split('.')
    if ((version[0] < 2 && version[1] < 9) || (version[0] == 1 && version[1] == 9 && version[2] < 1) || (version[0] > 3)) {
      throw new Error('Bootstrap\'s JavaScript requires jQuery version 1.9.1 or higher, but lower than version 4')
    }
  }(jQuery);
  
  /* ========================================================================
   * Bootstrap: button.js v3.3.7
   * http://getbootstrap.com/javascript/#buttons
   * ========================================================================
   * Copyright 2011-2016 Twitter, Inc.
   * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
   * ======================================================================== */
  
  
  +function ($) {
    'use strict';
  
    // BUTTON PUBLIC CLASS DEFINITION
    // ==============================
  
    var Button = function (element, options) {
      this.$element  = $(element)
      this.options   = $.extend({}, Button.DEFAULTS, options)
      this.isLoading = false
    }
  
    Button.VERSION  = '3.3.7'
  
    Button.DEFAULTS = {
      loadingText: 'loading...'
    }
  
    Button.prototype.setState = function (state) {
      var d    = 'disabled'
      var $el  = this.$element
      var val  = $el.is('input') ? 'val' : 'html'
      var data = $el.data()
  
      state += 'Text'
  
      if (data.resetText == null) $el.data('resetText', $el[val]())
  
      // push to event loop to allow forms to submit
      setTimeout($.proxy(function () {
        $el[val](data[state] == null ? this.options[state] : data[state])
  
        if (state == 'loadingText') {
          this.isLoading = true
          $el.addClass(d).attr(d, d).prop(d, true)
        } else if (this.isLoading) {
          this.isLoading = false
          $el.removeClass(d).removeAttr(d).prop(d, false)
        }
      }, this), 0)
    }
  
    Button.prototype.toggle = function () {
      var changed = true
      var $parent = this.$element.closest('[data-toggle="buttons"]')
  
      if ($parent.length) {
        var $input = this.$element.find('input')
        if ($input.prop('type') == 'radio') {
          if ($input.prop('checked')) changed = false
          $parent.find('.active').removeClass('active')
          this.$element.addClass('active')
        } else if ($input.prop('type') == 'checkbox') {
          if (($input.prop('checked')) !== this.$element.hasClass('active')) changed = false
          this.$element.toggleClass('active')
        }
        $input.prop('checked', this.$element.hasClass('active'))
        if (changed) $input.trigger('change')
      } else {
        this.$element.attr('aria-pressed', !this.$element.hasClass('active'))
        this.$element.toggleClass('active')
      }
    }
  
  
    // BUTTON PLUGIN DEFINITION
    // ========================
  
    function Plugin(option) {
      return this.each(function () {
        var $this   = $(this)
        var data    = $this.data('bs.button')
        var options = typeof option == 'object' && option
  
        if (!data) $this.data('bs.button', (data = new Button(this, options)))
  
        if (option == 'toggle') data.toggle()
        else if (option) data.setState(option)
      })
    }
  
    var old = $.fn.button
  
    $.fn.button             = Plugin
    $.fn.button.Constructor = Button
  
  
    // BUTTON NO CONFLICT
    // ==================
  
    $.fn.button.noConflict = function () {
      $.fn.button = old
      return this
    }
  
  
    // BUTTON DATA-API
    // ===============
  
    $(document)
      .on('click.bs.button.data-api', '[data-toggle^="button"]', function (e) {
        var $btn = $(e.target).closest('.btn')
        Plugin.call($btn, 'toggle')
        if (!($(e.target).is('input[type="radio"], input[type="checkbox"]'))) {
          // Prevent double click on radios, and the double selections (so cancellation) on checkboxes
          e.preventDefault()
          // The target component still receive the focus
          if ($btn.is('input,button')) $btn.trigger('focus')
          else $btn.find('input:visible,button:visible').first().trigger('focus')
        }
      })
      .on('focus.bs.button.data-api blur.bs.button.data-api', '[data-toggle^="button"]', function (e) {
        $(e.target).closest('.btn').toggleClass('focus', /^focus(in)?$/.test(e.type))
      })
  
  }(jQuery);
  
  /* ========================================================================
   * Bootstrap: modal.js v3.3.7
   * http://getbootstrap.com/javascript/#modals
   * ========================================================================
   * Copyright 2011-2016 Twitter, Inc.
   * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
   * ======================================================================== */
  
  
  +function ($) {
    'use strict';
  
    // MODAL CLASS DEFINITION
    // ======================
  
    var Modal = function (element, options) {
      this.options             = options
      this.$body               = $(document.body)
      this.$element            = $(element)
      this.$dialog             = this.$element.find('.modal-dialog')
      this.$backdrop           = null
      this.isShown             = null
      this.originalBodyPad     = null
      this.scrollbarWidth      = 0
      this.ignoreBackdropClick = false
  
      if (this.options.remote) {
        this.$element
          .find('.modal-content')
          .load(this.options.remote, $.proxy(function () {
            this.$element.trigger('loaded.bs.modal')
          }, this))
      }
    }
  
    Modal.VERSION  = '3.3.7'
  
    Modal.TRANSITION_DURATION = 300
    Modal.BACKDROP_TRANSITION_DURATION = 150
  
    Modal.DEFAULTS = {
      backdrop: true,
      keyboard: true,
      show: true
    }
  
    Modal.prototype.toggle = function (_relatedTarget) {
      return this.isShown ? this.hide() : this.show(_relatedTarget)
    }
  
    Modal.prototype.show = function (_relatedTarget) {
      var that = this
      var e    = $.Event('show.bs.modal', { relatedTarget: _relatedTarget })
  
      this.$element.trigger(e)
  
      if (this.isShown || e.isDefaultPrevented()) return
  
      this.isShown = true
  
      this.checkScrollbar()
      this.setScrollbar()
      this.$body.addClass('modal-open')
  
      this.escape()
      this.resize()
  
      this.$element.on('click.dismiss.bs.modal', '[data-dismiss="modal"]', $.proxy(this.hide, this))
  
      this.$dialog.on('mousedown.dismiss.bs.modal', function () {
        that.$element.one('mouseup.dismiss.bs.modal', function (e) {
          if ($(e.target).is(that.$element)) that.ignoreBackdropClick = true
        })
      })
  
      this.backdrop(function () {
        var transition = $.support.transition && that.$element.hasClass('fade')
  
        if (!that.$element.parent().length) {
          that.$element.appendTo(that.$body) // don't move modals dom position
        }
  
        that.$element
          .show()
          .scrollTop(0)
  
        that.adjustDialog()
  
        if (transition) {
          that.$element[0].offsetWidth // force reflow
        }
  
        that.$element.addClass('in')
  
        that.enforceFocus()
  
        var e = $.Event('shown.bs.modal', { relatedTarget: _relatedTarget })
  
        transition ?
          that.$dialog // wait for modal to slide in
            .one('bsTransitionEnd', function () {
              that.$element.trigger('focus').trigger(e)
            })
            .emulateTransitionEnd(Modal.TRANSITION_DURATION) :
          that.$element.trigger('focus').trigger(e)
      })
    }
  
    Modal.prototype.hide = function (e) {
      if (e) e.preventDefault()
  
      e = $.Event('hide.bs.modal')
  
      this.$element.trigger(e)
  
      if (!this.isShown || e.isDefaultPrevented()) return
  
      this.isShown = false
  
      this.escape()
      this.resize()
  
      $(document).off('focusin.bs.modal')
  
      this.$element
        .removeClass('in')
        .off('click.dismiss.bs.modal')
        .off('mouseup.dismiss.bs.modal')
  
      this.$dialog.off('mousedown.dismiss.bs.modal')
  
      $.support.transition && this.$element.hasClass('fade') ?
        this.$element
          .one('bsTransitionEnd', $.proxy(this.hideModal, this))
          .emulateTransitionEnd(Modal.TRANSITION_DURATION) :
        this.hideModal()
    }
  
    Modal.prototype.enforceFocus = function () {
      $(document)
        .off('focusin.bs.modal') // guard against infinite focus loop
        .on('focusin.bs.modal', $.proxy(function (e) {
          if (document !== e.target &&
              this.$element[0] !== e.target &&
              !this.$element.has(e.target).length) {
            this.$element.trigger('focus')
          }
        }, this))
    }
  
    Modal.prototype.escape = function () {
      if (this.isShown && this.options.keyboard) {
        this.$element.on('keydown.dismiss.bs.modal', $.proxy(function (e) {
          e.which == 27 && this.hide()
        }, this))
      } else if (!this.isShown) {
        this.$element.off('keydown.dismiss.bs.modal')
      }
    }
  
    Modal.prototype.resize = function () {
      if (this.isShown) {
        $(window).on('resize.bs.modal', $.proxy(this.handleUpdate, this))
      } else {
        $(window).off('resize.bs.modal')
      }
    }
  
    Modal.prototype.hideModal = function () {
      var that = this
      this.$element.hide()
      this.backdrop(function () {
        that.$body.removeClass('modal-open')
        that.resetAdjustments()
        that.resetScrollbar()
        that.$element.trigger('hidden.bs.modal')
      })
    }
  
    Modal.prototype.removeBackdrop = function () {
      this.$backdrop && this.$backdrop.remove()
      this.$backdrop = null
    }
  
    Modal.prototype.backdrop = function (callback) {
      var that = this
      var animate = this.$element.hasClass('fade') ? 'fade' : ''
  
      if (this.isShown && this.options.backdrop) {
        var doAnimate = $.support.transition && animate
  
        this.$backdrop = $(document.createElement('div'))
          .addClass('modal-backdrop ' + animate)
          .appendTo(this.$body)
  
        this.$element.on('click.dismiss.bs.modal', $.proxy(function (e) {
          if (this.ignoreBackdropClick) {
            this.ignoreBackdropClick = false
            return
          }
          if (e.target !== e.currentTarget) return
          this.options.backdrop == 'static'
            ? this.$element[0].focus()
            : this.hide()
        }, this))
  
        if (doAnimate) this.$backdrop[0].offsetWidth // force reflow
  
        this.$backdrop.addClass('in')
  
        if (!callback) return
  
        doAnimate ?
          this.$backdrop
            .one('bsTransitionEnd', callback)
            .emulateTransitionEnd(Modal.BACKDROP_TRANSITION_DURATION) :
          callback()
  
      } else if (!this.isShown && this.$backdrop) {
        this.$backdrop.removeClass('in')
  
        var callbackRemove = function () {
          that.removeBackdrop()
          callback && callback()
        }
        $.support.transition && this.$element.hasClass('fade') ?
          this.$backdrop
            .one('bsTransitionEnd', callbackRemove)
            .emulateTransitionEnd(Modal.BACKDROP_TRANSITION_DURATION) :
          callbackRemove()
  
      } else if (callback) {
        callback()
      }
    }
  
    // these following methods are used to handle overflowing modals
  
    Modal.prototype.handleUpdate = function () {
      this.adjustDialog()
    }
  
    Modal.prototype.adjustDialog = function () {
      var modalIsOverflowing = this.$element[0].scrollHeight > document.documentElement.clientHeight
  
      this.$element.css({
        paddingLeft:  !this.bodyIsOverflowing && modalIsOverflowing ? this.scrollbarWidth : '',
        paddingRight: this.bodyIsOverflowing && !modalIsOverflowing ? this.scrollbarWidth : ''
      })
    }
  
    Modal.prototype.resetAdjustments = function () {
      this.$element.css({
        paddingLeft: '',
        paddingRight: ''
      })
    }
  
    Modal.prototype.checkScrollbar = function () {
      var fullWindowWidth = window.innerWidth
      if (!fullWindowWidth) { // workaround for missing window.innerWidth in IE8
        var documentElementRect = document.documentElement.getBoundingClientRect()
        fullWindowWidth = documentElementRect.right - Math.abs(documentElementRect.left)
      }
      this.bodyIsOverflowing = document.body.clientWidth < fullWindowWidth
      this.scrollbarWidth = this.measureScrollbar()
    }
  
    Modal.prototype.setScrollbar = function () {
      var bodyPad = parseInt((this.$body.css('padding-right') || 0), 10)
      this.originalBodyPad = document.body.style.paddingRight || ''
      if (this.bodyIsOverflowing) this.$body.css('padding-right', bodyPad + this.scrollbarWidth)
    }
  
    Modal.prototype.resetScrollbar = function () {
      this.$body.css('padding-right', this.originalBodyPad)
    }
  
    Modal.prototype.measureScrollbar = function () { // thx walsh
      var scrollDiv = document.createElement('div')
      scrollDiv.className = 'modal-scrollbar-measure'
      this.$body.append(scrollDiv)
      var scrollbarWidth = scrollDiv.offsetWidth - scrollDiv.clientWidth
      this.$body[0].removeChild(scrollDiv)
      return scrollbarWidth
    }
  
  
    // MODAL PLUGIN DEFINITION
    // =======================
  
    function Plugin(option, _relatedTarget) {
      return this.each(function () {
        var $this   = $(this)
        var data    = $this.data('bs.modal')
        var options = $.extend({}, Modal.DEFAULTS, $this.data(), typeof option == 'object' && option)
  
        if (!data) $this.data('bs.modal', (data = new Modal(this, options)))
        if (typeof option == 'string') data[option](_relatedTarget)
        else if (options.show) data.show(_relatedTarget)
      })
    }
  
    var old = $.fn.modal
  
    $.fn.modal             = Plugin
    $.fn.modal.Constructor = Modal
  
  
    // MODAL NO CONFLICT
    // =================
  
    $.fn.modal.noConflict = function () {
      $.fn.modal = old
      return this
    }
  
  
    // MODAL DATA-API
    // ==============
  
    $(document).on('click.bs.modal.data-api', '[data-toggle="modal"]', function (e) {
      var $this   = $(this)
      var href    = $this.attr('href')
      var $target = $($this.attr('data-target') || (href && href.replace(/.*(?=#[^\s]+$)/, ''))) // strip for ie7
      var option  = $target.data('bs.modal') ? 'toggle' : $.extend({ remote: !/#/.test(href) && href }, $target.data(), $this.data())
  
      if ($this.is('a')) e.preventDefault()
  
      $target.one('show.bs.modal', function (showEvent) {
        if (showEvent.isDefaultPrevented()) return // only register focus restorer if modal will actually get shown
        $target.one('hidden.bs.modal', function () {
          $this.is(':visible') && $this.trigger('focus')
        })
      })
      Plugin.call($target, option, this)
    })
  
  }(jQuery);  