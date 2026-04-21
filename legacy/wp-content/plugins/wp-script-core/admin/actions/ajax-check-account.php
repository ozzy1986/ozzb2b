<?php
/**
 * Ajax Method to check user account.
 *
 * @api
 * @package CORE\admin\actions
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Check if the user account already exists or not
 *
 * @return void
 */
function wpscore_check_account() {
	check_ajax_referer( 'ajax-nonce', 'nonce' );

	if ( ! isset( $_POST['email'] ) ) {
		wp_die( 'email needed' );
	}

	if ( isset( $_POST['license_key'] ) ) {
		wp_die( 'license_key needed' );
	}

	$license_key = sanitize_text_field( wp_unslash( $_POST['license_key'] ) );

	$api_params = array(
		'core_version' => WPSCORE_VERSION,
		'server_addr'  => WPSCORE()->get_server_addr(),
		'server_name'  => WPSCORE()->get_server_name(),
		'signature'    => WPSCORE()->get_client_signature(),
		'time'         => ceil( time() / 1000 ), // 100
		'email'        => sanitize_email( wp_unslash( $_POST['email'] ) ),
	);

	$args = array(
		'timeout'   => 10,
		'sslverify' => false,
	);

	$base64_params = base64_encode( serialize( $api_params ) );

	// Send the request.
	$response = wp_remote_get( WPSCORE()->get_api_url( 'check_account', $base64_params ), $args );

	if ( ! is_wp_error( $response ) && strpos( $response['headers']['content-type'], 'application/json' ) !== false ) {

		$response_body = json_decode( wp_remote_retrieve_body( $response ) );

		if ( 200 !== $response_body->data->status ) {
			WPSCORE()->write_log( 'error', 'Connection to API (check_account) failed (status: <code>' . $response_body->data->status . '</code> message: <code>' . $response_body->message . '</code>)', __FILE__, __LINE__ );

		} else {

			if ( 'success' === $response_body->code ) {
				WPSCORE()->update_license_key( $response_body->data->license );
				WPSCORE()->init( true );
				WPSCORE()->write_log( 'success', 'License Key changed <code>' . $license_key . '</code>', __FILE__, __LINE__ );
			} else {
				WPSCORE()->write_log( 'error', 'Connection to API (check_account) failed (status: <code>' . $response_body->data->status . '</code> message: <code>' . $response_body->message . '</code>)', __FILE__, __LINE__ );
			}
		}

		wp_send_json( $response_body );

	} else {
		WPSCORE()->update_license_key( '' );
		$message = wp_json_encode( $response );
		WPSCORE()->write_log( 'error', 'Connection to API (check_account) failed (status: <code>' . $message . '</code>)', __FILE__, __LINE__ );
		if ( strpos( $message, 'cURL error 35' ) !== false ) {
			$message = 'Please update your cUrl version';
		}
		$output = array(
			'code'    => 'error',
			'message' => $message,
		);
		wp_send_json( $output );
	}
	wp_die();

}
add_action( 'wp_ajax_wpscore_check_account', 'wpscore_check_account' );
