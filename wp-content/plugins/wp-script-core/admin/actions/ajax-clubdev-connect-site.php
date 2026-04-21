<?php
/**
 * Ajax Method to connect site to clubdev.
 *
 * @api
 * @deprecated
 * @package admin\actions
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Connect site to WPS Gold.
 *
 * @return void
 */
function wpscore_wpsgold_connect_site() {
	check_ajax_referer( 'ajax-nonce', 'nonce' );

	$api_params = array(
		'core_version' => WPSCORE_VERSION,
		'license_key'  => WPSCORE()->get_license_key(),
		'server_addr'  => WPSCORE()->get_server_addr(),
		'server_name'  => WPSCORE()->get_server_name(),
		'signature'    => WPSCORE()->get_client_signature(),
		'time'         => ceil( time() / 1000 ), // 100
	);

	$args = array(
		'timeout'   => 10,
		'sslverify' => false,
	);

	$base64_params = base64_encode( serialize( $api_params ) );

	// Send the request.
	$response = wp_remote_get( WPSCORE()->get_api_url( 'wpsgold_connect_site', $base64_params ), $args );

	if ( ! is_wp_error( $response ) && strpos( $response['headers']['content-type'], 'application/json' ) !== false ) {

		$response_body = json_decode( wp_remote_retrieve_body( $response ) );

		if ( 200 !== $response_body->data->status ) {
			WPSCORE()->write_log( 'error', 'Connection to API (wpsgold_connect_site) failed (status: <code>' . $response_body->data->status . '</code> message: <code>' . $response_body->message . '</code>)', __FILE__, __LINE__ );
		} else {
			if ( 'success' === $response_body->code ) {
				WPSCORE()->write_log( 'success', 'Site connected with WP-Script GOLD</code>', __FILE__, __LINE__ );
			} else {
				WPSCORE()->write_log( 'error', 'Connection to API (wpsgold_connect_site) failed (status: <code>' . $response_body->data->status . '</code> message: <code>' . $response_body->message . '</code>)', __FILE__, __LINE__ );
			}
		}
	}

	wp_send_json( $response_body );

	wp_die();
}
add_action( 'wp_ajax_wpscore_wpsgold_connect_site', 'wpscore_wpsgold_connect_site' );
