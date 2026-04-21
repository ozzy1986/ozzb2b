<?php
/**
 * Ajax Method to delete logs data.
 *
 * @api
 * @package admin\actions
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Delete WP-Script Core logs.
 *
 * @return void
 */
function wpscore_delete_logs() {
	check_ajax_referer( 'ajax-nonce', 'nonce' );
	wpscore_log()->delete_logs();
	wp_die();
}
add_action( 'wp_ajax_wpscore_delete_logs', 'wpscore_delete_logs' );
