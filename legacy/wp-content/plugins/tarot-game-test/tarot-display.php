<?php

$output = ''; // this defines the output to replace the shortcode


// generate number of cards in result
$result_cards = array();
$number_of_cards = get_option( 'tarot_cards_number' );
if ( empty( $number_of_cards ) ) {
	$number_of_cards = 5;
}
for ( $i=1; $i <= $number_of_cards; $i++ ) {
	$result_cards[] = '<div class="card_empty" id="empty' . $i . '"></div>';
}
$result_cards = implode( "\n", $result_cards );

// cover image for cards
$cover = get_option( 'tarot_cover_image' );
if ( empty( $cover ) ) {
	$cover = plugin_dir_url( __FILE__ ) . 'images/cards/cover.png';
} else {
	$cover_image_attributes = wp_get_attachment_image_src( $cover, 'medium'	);
	//echo '<pre>' . print_r( $cover_image_attributes, true ) . '</pre>';
	$cover = $cover_image_attributes[0];
}

// generate whole deck
$deck = array();
$tarot_card_images = get_option( 'tarot_card_images' );
//echo '<div>tarot_card_images<pre>' . print_r( $tarot_card_images, true ) . '</pre></div>'; exit;
foreach ( $tarot_card_images as $id => $card_url ) {
	$deck[] = '<div class="card" id="' . $id . '" data-value="' . $id . '" style="background-image: url(\'' . $cover . '\');"></div>';
}
$deck = implode( "\n", $deck );

// HTML above the cards before the draw
//$html_before_above = get_option('tarot_html_above_before_draw');
// HTML below the cards before the draw
//$html_before_below = get_option('tarot_html_below_before_draw');
// HTML above the cards after the draw
//$html_after_above = get_option('tarot_html_above_after_draw');
// HTML below the cards after the draw
//$html_after_below = get_option('tarot_html_below_after_draw');


ob_start();
?>
<script type="text/javascript">
	var pluginDir			= "<?php echo plugin_dir_url( __FILE__ ); ?>";
	//var htmlAfterAbove	= '<?php //echo $html_after_above; ?>';
	var htmlAfterBelow		= `<?php echo $tarot_shortcode_parameters['below_after']; ?>`;
	var cardImages			= `<?php echo json_encode( $tarot_card_images ); ?>`;
	var numberOfCards		= `<?php echo $number_of_cards; ?>`;
</script>

<div class="containerTarot">

	<div class="above"><?php echo $tarot_shortcode_parameters['above_before']; ?></div>
	
	<div class="tarotGame">
	
		<div id="tarot_deck">
			<?php echo $deck; ?>
		</div>
		
		<div class="below"><?php echo $tarot_shortcode_parameters['below_before']; ?></div>
		<div class="below_after blinking">&nbsp;</div>
		
		<div class="result_cards"><?php echo $result_cards; ?></div>
			
	</div>

</div>
<?php
$output = ob_get_contents();
ob_clean();
?>