<?php
/**
 * @since             1.0.0
 * @package           Woodurcoin
 *
 * @wordpress-plugin
 * Plugin Name:       Woodurcoin
 * Plugin URI:        https://github.com/granvik/woodurcoin/
 * Description:       Integration Durcoin payments into Woocommerce.
 * Version:           1.0.0
 * Author:            granvik
 * Author URI:        https://aradm.ru/
 * License:           GPL
 * License URI:       GPL
 * Text Domain:       woodurcoin
 * Domain Path:       /languages
 */

// If this file is called directly, abort.
if (!defined('WPINC')) {
    die;
}

if (!in_array('woocommerce/woocommerce.php', apply_filters('active_plugins', get_option('active_plugins')))) {
    return;
}

// The plugin needs a gmp extension
if (!extension_loaded('gmp')) {
    $error_message = __('This plugin requires <a href="https://www.php.net/manual/en/book.gmp.php" target="_blank">GMP PHP extension</a>.', 'woodurcoin');
    die($error_message);
}

define('WOODURCOIN_VERSION', '1.0.0');

add_action('plugins_loaded', 'woodurcoin_init', 11);

function woodurcoin_init()
{
    if (class_exists('WC_Payment_Gateway')) {
        require_once plugin_dir_path(__FILE__) . '/includes/class-woodurcoin.php';
        require_once plugin_dir_path(__FILE__) . '/includes/class-waves-nodes.php';
        require_once plugin_dir_path(__FILE__) . '/includes/class-waves-exchange.php';
        require_once plugin_dir_path(__FILE__) . '/includes/class-cbr-exchange.php';
        require_once __DIR__ . '/vendor/autoload.php';
        add_filter('woocommerce_payment_gateways', 'add_to_woo_woodurcoin_payment_gateway');
        add_filter('query_vars', 'add_woodurcoin_query_vars');
        add_action('parse_request', 'woodurcoin_url_handler');
        add_action('init', 'woodurcoin_load_plugin_textdomain');
    }
}

function add_to_woo_woodurcoin_payment_gateway($gateways)
{
    $gateways[] = 'WC_Gateway_Woodurcoin';
    return $gateways;
}

function add_woodurcoin_query_vars($vars)
{
    $vars[] = "txId";
    return $vars;
}

function woodurcoin_url_handler()
{
    if (!empty($_GET['txId'])) {
        if (false !== strpos($_SERVER['REQUEST_URI'], 'woodurcoin-pay-order-')) {
            $txId = $_GET['txId'];
            $order_id = preg_replace('/.*woodurcoin-pay-order-(\d*).*/', '$1', $_SERVER['REQUEST_URI']);
            $order = wc_get_order($order_id);
            wp_redirect($order->get_checkout_payment_url() . '&txId=' . $txId);
            exit();
        }
    }
}

function woodurcoin_load_plugin_textdomain()
{
    load_plugin_textdomain(
        'woodurcoin',
        false,
        dirname(plugin_basename(__FILE__)) . '/languages/'
    );
}

