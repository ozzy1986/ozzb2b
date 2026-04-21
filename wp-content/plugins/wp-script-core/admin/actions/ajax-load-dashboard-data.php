<?php
/**
 * Ajax Method to load dashboard data.
 *
 * @api
 * @package admin\actions
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Load dashboard page data.
 *
 * @return void
 */
function wpscore_load_dashboard_data() {
	check_ajax_referer( 'ajax-nonce', 'nonce' );
	$current_user = wp_get_current_user();
	$data         = array(
		'user_email'         => $current_user->user_email,
		'core'               => WPSCORE()->get_core_options(),
		'installed_products' => WPSCORE()->get_installed_products(),
		'wps_gold'           => WPSCORE()->get_option( 'wpsgold' ),
		'products'           => WPSCORE()->get_products_options( array( 'data', 'eval' ) ),
		'user_license'       => WPSCORE()->get_license_key(),
	);
	wp_send_json( $data );
	wp_die();
}
add_action( 'wp_ajax_wpscore_load_dashboard_data', 'wpscore_load_dashboard_data' );
