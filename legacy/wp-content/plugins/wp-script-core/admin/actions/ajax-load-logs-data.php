<?php
/**
 * Ajax Method to load logs data.
 *
 * @api
 * @package Core\admin\actions
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Load the log page data.
 *
 * @return void
 */
function wpscore_load_logs_data() {
	check_ajax_referer( 'ajax-nonce', 'nonce' );
	$data         = array();
	$data['logs'] = wpscore_log()->get_logs();
	wp_send_json( $data );
	wp_die();
}
add_action( 'wp_ajax_wpscore_load_logs_data', 'wpscore_load_logs_data' );
