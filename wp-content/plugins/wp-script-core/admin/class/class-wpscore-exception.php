<?php
/**
 * WPSCORE_Exception Singleton Class.
 *
 * @package \admin\class\WPSCORE_Exception
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

if ( ! class_exists( 'WPSCORE_Exception' ) ) {
	/**
	 * WPSCORE_Exception Singleton Class.
	 *
	 * @since 1.3.9
	 */
	class WPSCORE_Exception extends Exception {
		/**
		 * Throw error.
		 * - write logs in all cases
		 * - display or not an admin notice depending on WPSCORE_DEBUG bool const.
		 *
		 * @return void
		 */
		public function throw_exception() {
			$this->write_wpscore_log();
			if ( true === WPSCORE_DEBUG ) {
				$this->display_admin_notice();
			}
		}

		/**
		 * Write current exception into WPSCORE logs.
		 *
		 * @return void
		 */
		public function write_wpscore_log() {
			wpscore_log()->write_log( 'error', $this->getMessage(), $this->getCode(), $this->getFile(), $this->getLine() );
		}

		/**
		 * Display admin notice.
		 *
		 * @return void
		 */
		public function display_admin_notice() {
			?>
				<div class="notice notice-error is-dismissible">
					<p><i><?php echo esc_html( $this->getMessage() ); ?></i> <small>( Error Code: <?php echo esc_html( $this->getCode() ); ?> )</small></p>
				</div>
			<?php
		}
	}
}
