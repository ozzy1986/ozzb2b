<?php
/**
 * Ajax Method to toggle theme activation.
 *
 * @api
 * @package admin\actions
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Toggle Theme within WP-Script Core dashboard.
 *
 * @return void
 */
function wpscore_toggle_theme() {
	check_ajax_referer( 'ajax-nonce', 'nonce' );

	if ( ! isset( $_POST['product_folder_slug'] ) ) {
		wp_die( 'product_folder_slug is missing!' );
	}

	switch_theme( sanitize_text_field( wp_unslash( $_POST['product_folder_slug'] ) ) );

	$output['product_state'] = 'activated';

	wp_send_json( $output );

	wp_die();
}
add_action( 'wp_ajax_wpscore_toggle_theme', 'wpscore_toggle_theme' );
