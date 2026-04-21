<?php
/**
 * Ajax Method to toggle plugin activation.
 *
 * @api
 * @package admin\actions
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Toggle Plugin within WP-Script Core dashboard.
 *
 * @return void
 */
function wpscore_toggle_plugin() {
	check_ajax_referer( 'ajax-nonce', 'nonce' );

	if ( ! isset( $_POST['product_folder_slug'] ) ) {
		wp_die( 'product_folder_slug is missing!' );
	}

	$product_folder_slug = sanitize_text_field( wp_unslash( $_POST['product_folder_slug'] ) );
	$plugin_path         = $product_folder_slug . '/' . $product_folder_slug . '.php';

	if ( ! is_plugin_active( $plugin_path ) ) {
		// Deactivation.
		$result = activate_plugin( $plugin_path );
		if ( ! is_wp_error( $result ) ) {
			$output['product_state'] = 'activated';
		} else {
			$output['error'] = true;
		}
	} else {
		// Activation.
		$result = deactivate_plugins( $plugin_path );
		if ( ! is_wp_error( $result ) ) {
			$output['product_state'] = 'deactivated';
		} else {
			$output['error'] = true;
		}
	}

	WPSCORE()->update_client_signature();

	wp_send_json( $output );
	wp_die();
}
add_action( 'wp_ajax_wpscore_toggle_plugin', 'wpscore_toggle_plugin' );
