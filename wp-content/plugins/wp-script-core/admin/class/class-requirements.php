<?php
/**
 * Requirements class
 *
 * @package wpscore\core\requirements
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * WPLC Requirements class.
 */
class WPSCORE_Requirements {

	/**
	 * Are all WPSCORE requirements ok?
	 *
	 * @return bool True if requirements are ok, false if not.
	 */
	public static function all_ok() {
		return self::curl_ok() && self::curl_version_ok();
	}

	/**
	 * Is PHP required version ok?
	 * - >= 5.3.0 since v1.0.0
	 * - >= 5.6.20 since v1.3.9
	 *
	 * @return bool True if PHP version is ok, false if not.
	 */
	public static function php_ok() {
		return version_compare( PHP_VERSION, WPSCORE_PHP_REQUIRED ) >= 0;
	}

	/**
	 * Is cUrl installed?
	 *
	 * @return bool True if cUrl is installed, false if not.
	 */
	public static function curl_ok() {
		return function_exists( 'curl_version' );
	}

	/**
	 * Get installed cUrl version.
	 *
	 * @return string The installed cUrl version.
	 */
	public static function get_curl_version() {
		$curl_infos = curl_version();
		return $curl_infos['version'];
	}

	/**
	 * Is cUrl required version installed?
	 *
	 * @return bool True if the cUrl installed version is ok, false if not.
	 */
	public static function curl_version_ok() {
		return version_compare( self::get_curl_version(), '7.34.0' ) >= 0;
	}

	/**
	 * Detect if Wordfence plugin is activated and its firewall set to enabled.
	 *
	 * @return boolean True if it is activated, false if not.
	 */
	public static function is_wordfence_activated() {
		if ( ! is_plugin_active( 'wordfence/wordfence.php' ) ) {
			return false;
		}
		$wordfence = wfWAF::getInstance()->getStorageEngine();
		return ( 'enabled' === $wordfence->getConfig( 'wafStatus' ) );
	}
}
