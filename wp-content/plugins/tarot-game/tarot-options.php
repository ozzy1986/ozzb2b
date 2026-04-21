<?php
// Save user's changes
if ( !empty( $_POST ) ) {
	//echo '<div>post<pre>' . print_r( $_POST, true ) . '</pre></div>';
}
if ( !empty( $_POST['save'] ) and check_admin_referer( 'tarot_upload_cards_' . get_current_user_id() ) ) {
	
	// save array of card images
	if ( !empty( $_POST['tarot_card_images'][1] ) ) {
		array_shift( $_POST['tarot_card_images'] ); // first element is always empty
		$tarot_card_images = array_map( 'esc_url_raw', $_POST['tarot_card_images']  ); // sanitize array of urls
		update_option( 'tarot_card_images', $tarot_card_images );
	}

	// save number of displayed cards
	if ( isset( $_POST['tarot_cards_number'] ) ) {
		$tarot_cards_number = absint( $_POST['tarot_cards_number'] ); // sanitize positive integer
		update_option( 'tarot_cards_number', $tarot_cards_number );
	}

	// save cover image for cards
	if ( isset( $_POST['tarot_cover_image'] ) ) {
		$tarot_cover_image = absint( $_POST['tarot_cover_image'] ); // sanitize positive integer (image id is passed)
		update_option( 'tarot_cover_image', $tarot_cover_image );
	}

	// save text that is shown above the cards before the draw
	if ( isset( $_POST['tarot_html_above_before_draw'] ) ) {
		$tarot_html_above_before_draw = sanitize_textarea_field( $_POST['tarot_html_above_before_draw'] ); // sanitize text
		update_option( 'tarot_html_above_before_draw', $tarot_html_above_before_draw );
	}
	// save text that is shown below the cards before the draw
	if ( isset( $_POST['tarot_html_below_before_draw'] ) ) {
		$tarot_html_below_before_draw = sanitize_textarea_field( $_POST['tarot_html_below_before_draw'] ); // sanitize text
		update_option( 'tarot_html_below_before_draw', $tarot_html_below_before_draw );
	}
	// save text that is shown below the cards after the draw
	if ( isset( $_POST['tarot_html_below_after_draw'] ) ) {
		$tarot_html_below_after_draw = sanitize_textarea_field( $_POST['tarot_html_below_after_draw'] ); // sanitize text
		update_option( 'tarot_html_below_after_draw', $tarot_html_below_after_draw );
	}
}

?>
<div class="wrap">

<h1>Choose options for Tarot Game</h1>
<form method="post" name="tarot_options" id="tarot_options" action="" enctype="multipart/form-data">

	<?php
	$tarot_card_images = get_option( 'tarot_card_images' );
	$tarot_card_images = array_filter( $tarot_card_images, function( $value ) { return $value !== ''; } );
	if ( !empty( $tarot_card_images ) ) {
		echo '<button type="submit" class="button" id="expand_deck">Expand deck</button>';
	}
	?>
	<div id="upload_cards" style="<?php echo ( !empty( $tarot_card_images ) ) ? 'display:none;' : ''; ?>">
		<div>
			<?php wp_nonce_field( 'tarot_upload_cards_' . get_current_user_id() ); ?>
			<input id="upload-button" type="button" class="button" value="Upload Card Images">
			<input type="hidden" name="tarot_card_images[]" value=""> <?php // this is needed if all images are deleted ?>
			<input type="checkbox" id="check_all"><label for="check_all">Check all</label>
			<div id="checked_action" style="display: none;">
				<a id="delete_many_cards" href="javascript: void(0);"> delete</a>
				<em></em>
			</div>
		</div>
		<?php
		foreach ( $tarot_card_images as $id => $url ) {
			$id++;
			$id_out = ( $id < 10 ) ? '&nbsp;' . $id . '&nbsp;' : $id;
			echo '<div class="tarot_card_image_preview" id="image_card_' . $id . '">
					<input type="hidden" name="tarot_card_images[]" value="' . esc_url( $url ) . '">
					<img src="' . esc_url( $url ) . '" width="138" height="240">
					<br>
					<label><em>' . $id_out . '</em>
						<input type="checkbox" class="check_row" name="selected_card_images[]" value="' . $id . '">
					</label>
					<button type="submit" class="remove_image button">Remove</button>
				</div>';
		}
		?>
	</div>
	<br>
	
	<table cellspacing="2" cellpadding="4">
	<tr>
		<td><label for="tarot_cards_number">Number of cards for the result of the draw.</label></td>
		<td><input type="number" min="3" max="9" name="tarot_cards_number" id="tarot_cards_number" value="<?php echo get_option('tarot_cards_number'); ?>"></td>
	</tr>
	<tr>
		<td><label for="tarot_cover_image">Choose the cover image.</label></td>
		<td><?php tarot_image_uploader( 'tarot_cover_image' ); ?></td>
	</tr>
	<tr>
		
		<td><label for="tarot_html_above_before_draw">The <strong>default</strong> HTML<br>above the cards deck before the draw.</label></td>
		<td>
			<?php wp_editor( get_option( 'tarot_html_above_before_draw' ), 'tarot_html_above_before_draw', array( 'textarea_rows' => 4, 'media_buttons' => false ) ); ?>
		</td>
	</tr>
	<tr>
		<td><label for="tarot_html_below_before_draw">The <strong>default</strong> HTML<br>below the cards deck before the draw.</label></td>
		<td>
			<?php wp_editor( get_option( 'tarot_html_below_before_draw' ), 'tarot_html_below_before_draw', array( 'textarea_rows' => 4, 'media_buttons' => false ) ); ?>
		</td>
	</tr>
	<?php /*<tr>
		<td><label for="tarot_html_above_after_draw">HTML above the cards deck after the draw</label></td>
		<td><?php wp_editor(get_option('tarot_html_above_after_draw'), 'tarot_html_above_after_draw', array('textarea_rows' => 4, 'media_buttons' => false)); ?></td>
	</tr>*/ ?>
	<tr>
		<td><label for="tarot_html_below_after_draw">The <strong>default</strong> HTML<br>below the cards deck after the draw.<br><br>With blinking effect.</label></td>
		<td>
			<?php wp_editor( get_option( 'tarot_html_below_after_draw' ), 'tarot_html_below_after_draw', array( 'textarea_rows' => 4, 'media_buttons' => false ) ); ?>
		</td>
	</tr>
	<?php /*<tr>
		<td><label for="tarot_responsive_height">Choose the responsive height, px</label></td>
		<td><input type="text" name="tarot_responsive_height" id="tarot_responsive_height" value="<?php echo get_option('tarot_responsive_height'); ?>"></td>
	</tr>
	<tr>
		<td><label for="tarot_responsive_width">Choose the responsive width, px</label></td>
		<td><input type="text" name="tarot_responsive_width" id="tarot_responsive_width" value="<?php echo get_option('tarot_responsive_width'); ?>"></td>
	</tr>*/ ?>
	<tr>
		<td colspan="2"><input type="submit" name="save" class="button button-primary save alignleft" value="Save"></td>
	</tr>
	</table>
</form>

</div>