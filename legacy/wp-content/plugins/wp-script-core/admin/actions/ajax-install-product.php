<?php
/**
 * Ajax Method to install produc (theme or plugin).
 *
 * @api
 * @package admin\actions
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Install / Update product within WP-Script Core dashboard.
 *
 * @return void
 */
function wpscore_install_product() {
	check_ajax_referer( 'ajax-nonce', 'nonce' );

	if ( ! isset( $_POST['method'], $_POST['product_type'], $_POST['product_sku'], $_POST['product_zip'], $_POST['product_slug'], $_POST['product_folder_slug'], $_POST['new_version'] ) ) {
		wp_die( 'Some parameters are missing!' );
	}

	$method              = sanitize_text_field( wp_unslash( $_POST['method'] ) );
	$product_type        = sanitize_text_field( wp_unslash( $_POST['product_type'] ) );
	$product_sku         = sanitize_text_field( wp_unslash( $_POST['product_sku'] ) );
	$product_zip         = sanitize_text_field( wp_unslash( $_POST['product_zip'] ) );
	$product_slug        = sanitize_text_field( wp_unslash( $_POST['product_slug'] ) );
	$product_folder_slug = sanitize_text_field( wp_unslash( $_POST['product_folder_slug'] ) );
	$new_version         = sanitize_text_field( wp_unslash( $_POST['new_version'] ) );

	$product   = array(
		'file_path'   => $product_folder_slug . '/' . $product_folder_slug . '.php',
		'package'     => $product_zip,
		'new_version' => $new_version,
		'slug'        => $product_slug,
	);
	$installer = new WPSCORE_Product_Uploader();
	$output    = $installer->upload_product( $product_type, $method, $product );

	// init installed products options.
	$options = array(
		'sku'               => $product_sku,
		'installed_version' => $new_version,
		'state'             => 'deactivated',
	);

	WPSCORE()->update_client_signature();

	wp_send_json( $output );
	wp_die();
}
add_action( 'wp_ajax_wpscore_install_product', 'wpscore_install_product' );
