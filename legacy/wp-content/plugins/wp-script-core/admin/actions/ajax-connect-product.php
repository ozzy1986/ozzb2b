<?php
/**
 * Ajax Method to connect product (theme or plugin).
 *
 * @api
 * @package admin\actions
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Connect product.
 *
 * @return void
 */
function wpscore_connect_product() {
	check_ajax_referer( 'ajax-nonce', 'nonce' );

	if ( ! isset( $_POST['product_type'], $_POST['product_sku'], $_POST['product_title'] ) ) {
		wp_die( 'parameter missing needed' );
	}

	$product_type  = sanitize_text_field( wp_unslash( $_POST['product_type'] ) );
	$product_sku   = sanitize_text_field( wp_unslash( $_POST['product_sku'] ) );
	$product_title = sanitize_text_field( wp_unslash( $_POST['product_title'] ) );

	$api_params = array(
		'core_version' => WPSCORE_VERSION,
		'license_key'  => WPSCORE()->get_license_key(),
		'product_sku'  => $product_sku,
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
	$response = wp_remote_get( WPSCORE()->get_api_url( 'connect_product', $base64_params ), $args );

	if ( ! is_wp_error( $response ) && strpos( $response['headers']['content-type'], 'application/json' ) !== false ) {

		$response_body = json_decode( wp_remote_retrieve_body( $response ) );

		if ( 200 !== $response_body->data->status ) {

			WPSCORE()->write_log( 'error', 'Connection to API (connect_product) failed (status: <code>' . $response_body->data->status . '</code> message: <code>' . $response_body->message . '</code>)', __FILE__, __LINE__ );

		} else {
			if ( 'success' === $response_body->code ) {
				WPSCORE()->update_product_status( $product_type, $product_sku, $response_body->data->product_status );
				WPSCORE()->write_log( 'success', 'Product connected <code>' . $product_title . '</code>', __FILE__, __LINE__ );
			} else {
				WPSCORE()->write_log( 'error', 'Connection to API (connect_product) failed (status: <code>' . $response_body->data->status . '</code> message: <code>' . $response_body->message . '</code>)', __FILE__, __LINE__ );
			}
		}
	} elseif ( is_wp_error( $response ) ) {
		WPSCORE()->write_log( 'error', $response->get_error_message() . ' <code>' . $response->get_error_code() . '</code>', WPSCORE_FILE, __LINE__ );
		return false;
	}

	wp_send_json( $response_body );

	wp_die();
}
add_action( 'wp_ajax_wpscore_connect_product', 'wpscore_connect_product' );
