function preloadImages(arguments) {
	console.log('arguments', arguments);
	for (var i = 0; i < arguments.length; i++) {
		//console.log(arguments[i]);
		jQuery('<img />').attr('src', arguments[i]);
	}
}

function blinker() {
	jQuery('.blinking').fadeOut(1000);
	jQuery('.blinking').fadeIn(1000);
}

function set_blinker() {
	setInterval(blinker, 1500);
}

// center the below text
function centerHtmls() {
	// Properly set .containerTarot height
	var innerHeight = jQuery('.above').outerHeight(true) + jQuery('.tarotGame').outerHeight(true);
	if (jQuery(window).width() < 700) {
		innerHeight *= 1.35;
	} else {
		innerHeight *= 0.9;
	}
	//console.log(innerHeight);
}

function rollHoriz() {
	//return false;
	var rollCards = 4;
	var cardWidth = Math.round(jQuery('.card').width() / jQuery('.card').parent().width() * 100).toFixed(2);
	jQuery('.card').each(function() {
		jQuery(this).css({ 'margin-right': '-' + (cardWidth - rollCards) + '%' });
	})
}


jQuery.fn.shuffle = function() {
	var obj = this.get();
	
	function randomize(obj) {
		return Math.floor(Math.random() * obj)
	}
	
	removeCard = jQuery.map(obj, function() {
		let temp	= randomize(obj.length);
		let	clone	= jQuery(obj[temp]).clone(!0)[0];
		obj.splice(temp, 1);
		
		return clone;
	});
	
	this.each(function(obj) {
		jQuery(this).replaceWith(jQuery(removeCard[obj]));
	});
	
	return jQuery(removeCard);
} 

jQuery(document).ready(function ($) {
	cardImages = $.parseJSON(cardImages);
	//preloadImages(cardImages);
	
	var topCard			= '0%';
	var	topCardHover	= '0%';
	var	cardCounter		= 0;
	var	selectedCards	= [];
	
	$('.tarotGame').innerHeight(100 * $('.tarotGame').innerWidth() / 100);
	$('div.card').shuffle();

	centerHtmls();
	rollHoriz();
	
	$('.card').mouseover(function() {
		$(this).addClass('hovered');
		$(this).css('top', topCardHover);
	});
	$('.card').mouseout(function() {
		$(this).removeClass('hovered');
		$(this).css('top', topCard);
	});

	console.log('cardImages', cardImages);
	console.log('numberOfCards', numberOfCards);
	console.log('cardCounter', cardCounter);
	$('.card').click(function() {
		cardCounter++;
		console.log('cardCounter', cardCounter);
		if (numberOfCards >= cardCounter) {
			var url = cardImages[$(this).attr('id')];
			$(this).css('display', 'none');
			$('#empty' + cardCounter).css('background-image', 'url(' + url + ')').css('background-size', '100% 100%');
			selectedCards.push($(this).attr('id'));
			
			if (numberOfCards == cardCounter) {
				$('.below_after').html(htmlAfterBelow);
				centerHtmls();
				set_blinker(); // in case you want a blinking message
			}
		}
	});
	
});

jQuery(window).resize(function() {
	centerHtmls();
});