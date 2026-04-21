<?php
/**
 * Plugin config file.
 *
 * @package CORE\Main
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

define( 'WPSCORE_DEBUG', false );
define( 'WPSCORE_VERSION', '2.0.7' );
define( 'WPSCORE_DIR', wp_normalize_path( plugin_dir_path( __FILE__ ) ) );
define( 'WPSCORE_URL', plugin_dir_url( __FILE__ ) );
define( 'WPSCORE_FILE', __FILE__ );
define( 'WPSCORE_LOG_FILE', wp_normalize_path( WPSCORE_DIR . 'admin' . DIRECTORY_SEPARATOR . 'logs' . DIRECTORY_SEPARATOR . 'wpscript.log' ) );
define( 'WPSCORE_API_URL', apply_filters( 'wpscore_api_url', 'https://www.wp-script.com/wp-json/wpsevsl/v2' ) );
define( 'WPSCORE_LOGO_URL', wp_normalize_path( WPSCORE_URL . 'admin' . DIRECTORY_SEPARATOR . 'assets' . DIRECTORY_SEPARATOR . 'images' . DIRECTORY_SEPARATOR . 'logo-wp-script.svg' ) );
define( 'WPSCORE_TWITTER_LOGO_URL', wp_normalize_path( WPSCORE_URL . 'admin' . DIRECTORY_SEPARATOR . 'assets' . DIRECTORY_SEPARATOR . 'images' . DIRECTORY_SEPARATOR . 'twitter.svg' ) );
define( 'WPSCORE_DISCORD_LOGO_URL', wp_normalize_path( WPSCORE_URL . 'admin' . DIRECTORY_SEPARATOR . 'assets' . DIRECTORY_SEPARATOR . 'images' . DIRECTORY_SEPARATOR . 'discord.svg' ) );
define( 'WPSCORE_NAME', 'WP-Script' );
define( 'WPSCORE_PHP_REQUIRED', '5.6.20' );

/**
 * Navigation config
 */
self::$config['nav'] = array(
	'0'    => array(
		'slug'     => 'wpscore-dashboard',
		'callback' => 'wpscore_dashboard_page',
		'title'    => 'Dashboard',
	),
	'1000' => array(
		'slug'     => 'wpscore-logs',
		'callback' => 'wpscore_logs_page',
		'title'    => 'Logs',
	),
);

/**
 * JS config
 */
self::$config['scripts']['js'] = array(
	// vendor.
	'WPSCORE_lodash.js'       => array(
		'in_pages'  => 'wpscript_pages',
		'path'      => 'admin/vendors/lodash/lodash.min.js',
		'require'   => array(),
		'version'   => '4.17.4',
		'in_footer' => false,
	),
	'WPSCORE_bootstrap.js'    => array(
		'in_pages'  => 'wpscript_pages',
		'path'      => 'admin/vendors/bootstrap/js/bootstrap.min.js',
		'require'   => array( 'jquery' ),
		'version'   => '3.2.0',
		'in_footer' => false,
	),
	'WPSCORE_vue.js'          => array(
		'in_pages'  => 'wpscript_pages',
		'path'      => 'admin/vendors/vue/vue.js',
		'require'   => array(),
		'version'   => '2.6.10',
		'in_footer' => false,
	),
	'WPSCORE_vue-resource.js' => array(
		'in_pages'  => 'wpscript_pages',
		'path'      => 'admin/vendors/vue-resource/vue-resource.min.js',
		'require'   => array(),
		'version'   => '1.0.3',
		'in_footer' => false,
	),
	'WPSCORE_vue-notify.js'   => array(
		'in_pages'  => 'wpscript_pages',
		'path'      => 'admin/vendors/vue-notify/vue-notify.min.js',
		'require'   => array(),
		'version'   => '3.2.1',
		'in_footer' => false,
	),
	'WPSCORE_clipboard.js'    => array(
		'in_pages'  => array( 'wpscore-logs' ),
		'path'      => 'admin/vendors/clipboard/clipboard.min.js',
		'require'   => array(),
		'version'   => '1.6.0',
		'in_footer' => false,
	),
	// pages.
	'WPSCORE_dashboard.js'    => array(
		'in_pages'  => array( 'wpscore-dashboard' ),
		'path'      => 'admin/pages/page-dashboard.js',
		'require'   => array(),
		'version'   => WPSCORE_VERSION,
		'in_footer' => false,
		'localize'  => array(
			'ajax'     => true,
			'base_url' => WPSCORE_URL,
			'i18n'     => array(
				'loading'                          => __( 'Loading', 'wpscore_lang' ),
				'loading_reloading'                => __( 'Reloading', 'wpscore_lang' ),

				'license__invalid'                 => __( 'Invalid License Key', 'wpscore_lang' ),

				'products__filter__all'            => __( 'All', 'wpscore_lang' ),
				'products__filter__connected'      => __( 'Connected', 'wpscore_lang' ),
				'products__filter__notConnected'   => __( 'Not connected', 'wpscore_lang' ),
				'products__filter__installed'      => __( 'Installed', 'wpscore_lang' ),
				'products__filter__notInstalled'   => __( 'Not installed', 'wpscore_lang' ),

				'product__version-installed'       => __( 'installed', 'wpscore_lang' ),
				'product__not-installed'           => __( 'Not installed', 'wpscore_lang' ),
				'product__comingSoon'              => __( 'Coming soon', 'wpscore_lang' ),
				'product__requirements'            => __( 'Req.', 'wpscore_lang' ),
				'product__connected'               => __( 'Connected', 'wpscore_lang' ),
				'product__notConnected'            => __( 'Not connected', 'wpscore_lang' ),

				'product__footer__purchase'        => __( 'Buy now', 'wpscore_lang' ),
				'product__footer__connect'         => __( 'Connect', 'wpscore_lang' ),
				'product__footer__install'         => __( 'Install', 'wpscore_lang' ),
				'product__footer__installing'      => __( 'Installing', 'wpscore_lang' ),
				'product__footer__updateTo'        => __( 'Update to', 'wpscore_lang' ),
				'product__footer__updatingTo'      => __( 'Updating to', 'wpscore_lang' ),
				'product__footer__activate'        => __( 'Activate', 'wpscore_lang' ),
				'product__footer__activating'      => __( 'Activating', 'wpscore_lang' ),
				'product__footer__deactivate'      => __( 'Deactivate', 'wpscore_lang' ),
				'product__footer__active_theme'    => __( 'Active theme', 'wpscore_lang' ),
				'product__footer__deactivating'    => __( 'Deactivating', 'wpscore_lang' ),
				'product__footer__reloading'       => __( 'Reloading', 'wpscore_lang' ),

				'gold__subscription_expired'       => __( 'Your WP-Script Gold subscription has expired. Reactivate it and get instant access to all existing and future WP-Script products', 'wpscore_lang' ),
				'gold__subscription_join'          => __( 'Join WP-Script Gold and get access to all existing and future WP-Script products', 'wpscore_lang' ),
				'gold__subscription_connect'       => __( 'Connect this site with your WP-Script Gold subscription and get instant access to all existing and future WP-Script products', 'wpscore_lang' ),
				'gold__subscription_limit-reached' => __( 'You\'ve reached the limit of sites you can connect with your current WP-Script Gold plan', 'wpscore_lang' ),
				'gold__button_join'                => __( 'Join WP-Script Gold', 'wpscore_lang' ),
				'gold__button_reactivate'          => __( 'Reactivate WP-Script Gold', 'wpscore_lang' ),
				'gold__button_upgrade'             => __( 'Upgrade WP-Script Gold plan', 'wpscore_lang' ),
				'gold__button_contact-us'          => __( 'Contact us', 'wpscore_lang' ),
			),
		),
	),
	'WPSCORE_logs.js'         => array(
		'in_pages'  => array( 'wpscore-logs' ),
		'path'      => 'admin/pages/page-logs.js',
		'require'   => array(),
		'version'   => WPSCORE_VERSION,
		'in_footer' => false,
		'localize'  => array(
			'ajax'       => true,
			'objectL10n' => array(),
		),
	),
);

/**
 *  CSS config.
 */
self::$config['scripts']['css'] = array(
	// vendor.
	'WPSCORE_fontawesome.css'           => array(
		'in_pages' => 'wpscript_pages',
		'path'     => 'admin/vendors/font-awesome/css/font-awesome.min.css',
		'require'  => array(),
		'version'  => '4.6.0',
		'media'    => 'all',
	),
	'WPSCORE_bootstrap.css'             => array(
		'in_pages' => 'wpscript_pages',
		'path'     => 'admin/vendors/bootstrap/css/bootstrap.min.css',
		'require'  => array(),
		'version'  => '3.2.0',
		'media'    => 'all',
	),
	'WPSCORE_bootstrap-4-utilities.css' => array(
		'in_pages' => 'wpscript_pages',
		'path'     => 'admin/vendors/bootstrap/css/bootstrap-4-utilities.min.css',
		'require'  => array( 'WPSCORE_bootstrap.css' ),
		'version'  => '1.0.0',
		'media'    => 'all',
	),
	'WPSCORE_vue-notify.css'            => array(
		'in_pages' => 'wpscript_pages',
		'path'     => 'admin/vendors/vue-notify/vue-notify.min.css',
		'require'  => array(),
		'version'  => '3.2.1',
		'media'    => 'all',
	),
	// assets.
	'WPSCORE_admin.css'                 => array(
		'in_pages' => 'wpscript_pages',
		'path'     => 'admin/assets/css/admin.css',
		'require'  => array(),
		'version'  => WPSCORE_VERSION,
		'media'    => 'all',
	),
	'WPSCORE_dashboard.css'             => array(
		'in_pages' => array( 'wpscore-dashboard' ),
		'path'     => 'admin/assets/css/dashboard.css',
		'require'  => array(),
		'version'  => WPSCORE_VERSION,
		'media'    => 'all',
	),
);
