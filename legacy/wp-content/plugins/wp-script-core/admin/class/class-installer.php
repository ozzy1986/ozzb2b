<?php
/**
 * Class installer
 *
 * @package CORE\Admin\Classes
 */

// Exit if accessed directly.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Installer Class
 *
 * @since 1.0.0
 */
class WPSCORE_Product_Uploader {

	/**
	 * The method to call (install/update)
	 *
	 * @var string
	 */
	private $method;

	/**
	 * The product SKU we want to install/update
	 *
	 * @var string;
	 */
	private $product;

	/**
	 * The type of product we want to install/update (theme/plugin)
	 *
	 * @var string
	 */
	private $type;

	/**
	 * Upload product to the server.
	 *
	 * @param string $type     The type of product to upload.
	 * @param string $method   The method to call (install/update).
	 * @param string $product  The product SKU.
	 *
	 * @return mixed The response of the called method or false if an issue occured.
	 */
	public function upload_product( $type, $method, $product ) {
		$this->product = $product;
		$this->method  = $method;
		$this->type    = $type;
		$response      = false;

		switch ( $type ) {
			case 'theme':
				// if user cannot install themes we die.
				if ( ! current_user_can( 'install_themes' ) ) {
					return __( 'You do not have sufficient permissions to install themes for this site.' );
				}
				$response = self::install_theme();
				break;

			case 'plugin':
				if ( ! current_user_can( 'install_plugins' ) ) {
					return __( 'You do not have sufficient permissions to install themes for this site.' );
				}
				$response = self::install_plugin();
				break;

			default:
				break;
		}
		return $response;
	}

	/**
	 * Install Theme function.
	 *
	 * @return mixed Installation response if succes, bool false if not.
	 */
	private function install_theme() {
		require_once ABSPATH . 'wp-admin/includes/admin.php';
		$upgrader = new Theme_Upgrader( new Theme_Quiet_Skin() );
		switch ( $this->method ) {
			case 'install':
				ob_start();
				$results = $upgrader->install( $this->product['package'] );
				$data    = ob_get_contents();
				ob_clean();
				break;
			case 'upgrade':
				ob_start();
				$results = $upgrader->upgrade( $this->product['slug'] );
				$data    = ob_get_contents();
				ob_clean();
				break;
			default:
				return false;
		}
		if ( ! $results ) {
			return $data;
		} else {
			return true;
		}
	}

	/**
	 * Install Plugin function.
	 *
	 * @return mixed Installation response if succes, bool false if not.
	 */
	private function install_plugin() {
		require_once ABSPATH . 'wp-admin/includes/admin.php';
		$upgrader = new Plugin_Upgrader( new Plugin_Quiet_Skin() );
		switch ( $this->method ) {
			case 'install':
				ob_start();
				$results = $upgrader->install( $this->product['package'] );
				$data    = ob_get_contents();
				ob_clean();
				break;
			case 'upgrade':
				self::inject_update_plugin_info();
				ob_start();
				$results = $upgrader->bulk_upgrade( array( $this->product['file_path'] ) );
				$data    = ob_get_contents();
				ob_clean();
				break;
			default:
				return false;
		}
		if ( ! $results ) {
			return $data;
		} else {
			return true;
		}
	}

	/**
	 * Clean up temp file on the server.
	 *
	 * @param string $file The file path to remove.
	 *
	 * @return void
	 */
	private function cleanup( $file ) {
		if ( file_exists( $file ) ) :
			unlink( $file );
		endif;
	}

	/**
	 * Inject theme infos after theme update.
	 *
	 * @return void
	 */
	private function inject_update_theme_info() {
		$repo_updates = get_site_transient( 'update_themes' );
		if ( ! is_object( $repo_updates ) ) {
			$repo_updates = new stdClass();
		}
		$slug = $this->product['slug'];
		// We only really need to set package, but let's do all we can in case WP changes something.
		$repo_updates->response[ $slug ]['theme']       = $this->product['slug'];
		$repo_updates->response[ $slug ]['new_version'] = $this->product['new_version'];
		$repo_updates->response[ $slug ]['package']     = $this->product['package'];
		$repo_updates->response[ $slug ]['url']         = 'https://www.wp-script.com';
		set_site_transient( 'update_themes', $repo_updates );
	}

	/**
	 * Inject plugin infos after plugin update.
	 *
	 * @return void
	 */
	private function inject_update_plugin_info() {
		$repo_updates = get_site_transient( 'update_plugins' );
		if ( ! is_object( $repo_updates ) ) {
			$repo_updates = new stdClass();
		}
		$file_path = $this->product['file_path'];
		if ( empty( $repo_updates->response[ $file_path ] ) ) {
			$repo_updates->response[ $file_path ] = new stdClass();
		}
		// We only really need to set package, but let's do all we can in case WP changes something.
		$repo_updates->response[ $file_path ]->slug        = $this->product['slug'];
		$repo_updates->response[ $file_path ]->plugin      = $this->product['file_path'];
		$repo_updates->response[ $file_path ]->new_version = $this->product['new_version'];
		$repo_updates->response[ $file_path ]->package     = $this->product['package'];
		$repo_updates->response[ $file_path ]->url         = 'https://www.wp-script.com';
		set_site_transient( 'update_plugins', $repo_updates );
	}

}

require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
class Plugin_Quiet_Skin extends Plugin_Installer_Skin {
	public function feedback( $string, ...$args ) {
		// just keep it quiet.
	}
}

class Theme_Quiet_Skin extends Theme_Installer_Skin {
	public function feedback( $string, ...$args ) {
		// just keep it quiet.
	}
}
