<?php
/**
 * Default page
 *
 * @package CORE\Admin\Pages
 */

// Exit if accessed directly.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * WPS CORE Dashboard page callback function
 *
 * @return void
 */
function wpscore_dashboard_page() {
	?>
	<div id="wp-script">
		<div class="content-tabs" id="dashboard">
			<?php WPSCORE()->display_logo(); ?>
			<?php WPSCORE()->display_tabs(); ?>
			<div class="tab-content">
				<div class="tab-pane active">
					<div v-cloak class="padding-top-15">
						<div class="row text-center v-cloak--block">
							<div class="col-xs-12 loading"><p><i class="fa fa-cog fa-spin fa-2x fa-fw" aria-hidden="true"></i><br><?php esc_html_e( 'Loading Core', 'wpscore_lang' ); ?>...</span></p></div>
						</div>
						<div class="v-cloak--hidden">
							<?php if ( WPSCORE_Requirements::is_wordfence_activated() ) : ?>
								<div class="row mb-5">
									<div class="col-xs-12 text-center">
										<div class="alert alert-info">
											<p class="mb-2"><strong><?php esc_html_e( 'Wordfence firewall is enabled', 'wpscore_lang' ); ?></strong></p>
												<p><?php esc_html_e( 'Wordfence Firewall mode is set to "enabled", which is amazing to protect your site.', 'wpscore_lang' ); ?></p>
												<p><?php esc_html_e( 'But this mode can prevent WP-Script plugins to work properly because of false positive.', 'wpscore_lang' ); ?> — <a target="_blank" rel="nofollow noreferrer" href="https://www.wordfence.com/help/firewall/#whitelisted-urls-and-false-positives"><?php esc_html_e( 'Learn more', 'wpscore_lang' ); ?></a></p>
											</div>
									</div>
								</div>
							<?php endif; ?>
							<?php if ( ! WPSCORE()->php_version_ok() ) : ?>
								<div class="row">
									<div class="col-xs-12 col-md-6 col-md-push-3">
										<h3 class="text-center"><?php esc_html_e( 'PHP > 5.3.0 is required', 'wpscore_lang' ); ?></h3>
										<div class="alert alert-danger">
											<?php /* translators: %s is the current too old installed PHP version */ ?>
											<p><strong>PHP >= <?php echo esc_html( WPSCORE_PHP_REQUIRED ); ?></strong> <?php printf( esc_html_x( 'is required to use WP-Script products. Your PHP version (%s) is too old. Please contact your hoster to update it', '[PHP version] is required...', 'wpscore_lang' ), PHP_VERSION ); ?></p>
										</div>
									</div>
								</div>
							<?php else : ?>
								<!--**************-->
								<!-- LOADING DATA -->
								<!--**************-->
								<template v-if="loading.loadingData">
									<div class="row text-center">
										<div class="col-xs-12 loading"><p><i class="fa fa-cog fa-spin-reverse fa-2x fa-fw" aria-hidden="true"></i><br><?php esc_html_e( 'Loading Data', 'wpscore_lang' ); ?>...</span></p></div>
									</div>
								</template>
								<transition name="fade">
									<div v-if="dataLoaded">
										<div v-if="core !== false" class="row">
											<div class="col-xs-12">
												<p class="core__version text-right">
													WP-Script Core v{{core.installed_version}}
													<template v-if="!core.is_latest_version">
														<button v-if="loading.updatingCore == false" @click="updateCore" class="btn btn-sm btn-success"><i class="fa fa-refresh" aria-hidden="true"></i> Update to v{{core.latest_version}}</button>
														<button v-if="loading.updatingCore == true" class="btn btn-sm btn-success disabled" disabled><i class="fa fa-cog fa-spin fa-fw" aria-hidden="true"></i> Updating to v{{core.latest_version}}</button>
														<button v-if="loading.updatingCore == 'activating'" class="btn btn-sm btn-success disabled" disabled><i class="fa fa-cog fa-spin fa-fw" aria-hidden="true"></i> Activating...</button>
														<button v-if="loading.updatingCore == 'reloading'" class="btn btn-sm btn-success disabled" disabled><i class="fa fa-cog fa-spin-reverse fa-fw" aria-hidden="true"></i> Reloading...</button>
													</template>
												</p>
											</div>
										</div>
										<!--***********************-->
										<!-- LICENSE NOT ACTIVATED -->
										<!--***********************-->
										<div v-if="!userLicense || loading.checkingLicense == 'reloading'">
											<div class="row">
												<div class="col-xs-12">
													<div class="alert text-center" v-bind:class="licenceBoxClass">
														<h3>
															<template v-if="loading.checkingLicense != 'reloading' && loading.checkingAccount != 'reloading' && !error"><?php esc_html_e( 'Activation required', 'wpscore_lang' ); ?></template>
															<template v-if="error">{{error}}</template>
															<template v-if="loading.checkingLicense == 'reloading' || loading.checkingAccount == 'reloading'"><?php esc_html_e( 'Activation Successful', 'wpscore_lang' ); ?> - <?php esc_html_e( 'Reloading', 'wpscore_lang' ); ?>...</template>
														</h3>
														<form action="" method="post">
															<div class="row">
																<div class="col-xs-12 col-md-6 col-lg-6 col-lg-push-3">
																	<div class="input-group">
																		<span class="input-group-addon"><span class="fa fa-unlock-alt"></span></span>
																		<input v-model="userLicenseInput" spellcheck="false" type="text" class="form-control check-license" placeholder="<?php esc_html_e( 'Paste your WP-Script License Key here', 'wpscore_lang' ); ?>" ref="refLicenseInput" />
																		<div class="input-group-btn">
																			<button @click.prevent="checkLicense" class="btn btn-default" v-bind:disabled="toggleLicenseBtn" type="submit">
																				<template v-if="loading.checkingLicense === true">
																					<i class="fa fa-cog fa-spin fa-fw" aria-hidden="true"></i> <?php esc_html_e( 'Activating License', 'wpscore_lang' ); ?>...
																				</template>
																				<template v-if="loading.checkingLicense == 'reloading'"><i class="fa fa-check text-success" aria-hidden="true"></i></template>
																				<template v-if="loading.checkingLicense === false"><?php esc_html_e( 'Activate my WP-Script License', 'wpscore_lang' ); ?></template>
																			</button>
																		</div>
																	</div>
																</div>
															</div>
														</form>
														<p class="margin-top-10 margin-bottom-20"><small><a href="https://www.wp-script.com/my-account/?utm_source=core&utm_medium=dashboard&utm_campaign=account&utm_content=getLicenseKey" title="<?php esc_html_e( 'Go to your WP-Script account to get your license key', 'wpscore_lang' ); ?>" target="_blank"><?php esc_html_e( 'Go to your WP-Script account to get your license key', 'wpscore_lang' ); ?></a></small></p>
														<button class="btn btn-transparent" type="button" data-toggle="collapse" data-target="#collapseExample" aria-expanded="false" aria-controls="collapseExample">
														<?php esc_html_e( "You don't have a WP-Script license yet?", 'wpscore_lang' ); ?>
														</button>
														<div class="collapse" id="collapseExample">
															<form id="form-check-account" action="" method="post">
																<div class="row padding-top-20">
																	<div class="col-xs-12 col-md-6 col-lg-6 col-lg-push-3">
																		<div class="input-group">
																			<span class="input-group-addon"><span class="fa fa-envelope"></span></span>
																			<input v-model="userEmailInput" type="text" class="form-control" value="" ref="refEmailInput"/>
																			<div class="input-group-btn">
																				<button @click.prevent="checkAccount" class="btn btn-default" type="submit">
																					<template v-if="loading.checkingAccount === true">
																						<i class="fa fa-cog fa-spin fa-fw" aria-hidden="true"></i> <?php esc_html_e( 'Creating account', 'wpscore_lang' ); ?>...
																					</template>
																					<template v-if="loading.checkingAccount == 'reloading'"><i class="fa fa-check text-success" aria-hidden="true"></i></template>
																					<template v-if="loading.checkingAccount === false"><?php esc_html_e( 'Create my WP-Script Account', 'wpscore_lang' ); ?></template>
																				</button>
																			</div>
																		</div>
																	</div>
																</div>
															</form>
															<p class="margin-top-10"><small><a rel="tooltip" data-html="true" data-original-title="<ul><li>–</li><li><?php esc_html_e( "You're going to create your unique WP-Script account", 'wpscore_lang' ); ?></li><li>–</li><li><?php esc_html_e( 'You will receive your login details to this email address', 'wpscore_lang' ); ?></li><li>–</li><li><?php esc_html_e( 'No spam', 'wpscore_lang' ); ?></li><li>–</li></ul>"><i class="fa fa-question-circle" aria-hidden="true"></i></span> <?php esc_html_e( 'More informations', 'wpscore_lang' ); ?></a></small></p>
														</div>
													</div>
												</div>
											</div>
										</div>
										<!--*******************-->
										<!-- LICENSE ACTIVATED -->
										<!--*******************-->
										<div v-else>
											<div class="row">
												<div class="col-xs-12">
													<div class="alert text-center p-4" v-bind:class="[wpsGold.site_connected ? 'wps-gold wps-gold-connected' : 'alert-license']">
														<template v-if="wpsGold.site_connected">
															<span class="text-gold wps-gold-text"><i class="fa fa-trophy" aria-hidden="true"></i> <?php esc_html_e( 'Site connected with WP-Script Gold', 'wpscore_lang' ); ?></span>
														</template>
														<p><strong><?php esc_html_e( 'Your WP-Script License Key', 'wpscore_lang' ); ?></strong></p>
														<div class="row padding-top-10 padding-bottom-10">
															<div class="col-xs-12 col-md-8 col-md-offset-2 col-lg-6 col-lg-offset-3">
																<div class="input-group">
																	<input spellcheck="false" type="text" class="form-control text-center" id="input-license" v-model="userLicenseInput" ref="refLicenseInput">
																	<span class="input-group-btn">
																		<button @click.prevent="checkLicense" class="btn btn-default" v-bind:class="{'disabled' : !userLicenseChanged}" v-bind:disabled="!userLicenseChanged" type="button"><i class="fa" v-bind:class="licenseButtonIconClass" aria-hidden="true"></i></button>
																	</span>
																</div>
															</div>
														</div>
													</div>
												</div>
											</div>

											<div v-if="!wpsGold.site_connected && wpsGold.current_plan >= 1 && wpsGold.time_remaining > 0" class="wps-gold wps-gold-not-connected text-center">
												<h2><i class="fa fa-trophy text-gold" aria-hidden="true"></i> <?php esc_html_e( 'WP-Script Gold', 'wpscore_lang' ); ?></h2>
												<p><a href="https://www.wp-script.com/gold/?utm_source=core&utm_medium=dashboard&utm_campaign=gold&utm_content=aboutGold" target="_blank"><?php esc_html_e( 'About WP-Script Gold', 'wpscore_lang' ); ?> <i class="fa fa-external-link" aria-hidden="true"></i></a></p>
												<p>{{wpsGoldSiteState.paragraph}}</p>
												<p>
													<template v-if="wpsGoldSiteState.linkHref">
														<a v-bind:href="wpsGoldSiteState.linkHref" class="btn btn-gold" target="_blank">
															<i v-bind:class="wpsGoldSiteState.iconClass" aria-hidden="true"></i> {{wpsGoldSiteState.buttonText}}
														</a>
													</template>
													<template v-else>
														<button @click.prevent="wpsGoldConnectSite" class="btn btn-gold">
															<i v-bind:class="wpsGoldSiteState.iconClass" aria-hidden="true"></i> {{wpsGoldSiteState.buttonText}}
														</button>
													</template>
												</p>
											</div>
											<products v-if="productsFromApi.themes" key="themes" v-bind:products="productsFromApi.themes" type="theme" v-bind:installed-products="installedProducts['themes']" v-bind:user-license="userLicense" v-bind:wps-gold-site-connected="wpsGold.site_connected"></products>
											<products v-if="productsFromApi.plugins" key="plugins" v-bind:products="productsFromApi.plugins" type="plugin" v-bind:installed-products="installedProducts['plugins']" v-bind:user-license="userLicense" v-bind:wps-gold-site-connected="wpsGold.site_connected"></products>
										</div>
									</div>
								</transition>
							<?php endif; ?>
						</div>
						<p class="text-right"><small>cUrl v<?php echo esc_html( WPSCORE()->get_curl_version() ); ?></small></p>
					</div>
				</div>
			</div>
			<?php WPSCORE()->display_footer(); ?>

			<!-- Create Connection Infos Modal -->
			<div class="modal fade" id="connection-infos-modal">
				<div class="modal-dialog modal-lg" role="document">
					<div class="modal-content">
						<div class="modal-header">
							<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only"><?php esc_html_e( 'Close', 'wpscore_lang' ); ?></span></button>
							<h4 class="modal-title text-center"><?php esc_html_e( 'How WP-Script products connection works?', 'wpscore_lang' ); ?></h4>
						</div>
						<div class="modal-body text-center">
							<div class="row">
								<p><?php esc_html_e( 'The button bellow each product will automatically change depending on which step you are.', 'wpscore_lang' ); ?></p>
								<div class="col-xs-12 col-md-6">
									<div class="thumbnail">
										<img src="<?php echo esc_url( WPSCORE_URL ); ?>admin/assets/images/product-connection-step-1.jpg">
										<div class="caption"><h5><strong>1.</strong> <?php esc_html_e( 'Purchase any product you need for 1 / 5 / ∞ sites', 'wpscore_lang' ); ?></h5></div>
									</div>
								</div>
								<div class="col-xs-12 col-md-6">
									<div class="thumbnail">
										<img src="<?php echo esc_url( WPSCORE_URL ); ?>admin/assets/images/product-connection-step-2.jpg">
										<div class="caption"><h5><strong>2.</strong> <?php esc_html_e( 'Connect the purchased product', 'wpscore_lang' ); ?></h5></div>
									</div>
								</div>
								<div class="col-xs-12 col-md-6">
									<div class="thumbnail">
										<img src="<?php echo esc_url( WPSCORE_URL ); ?>admin/assets/images/product-connection-step-3.jpg">
										<div class="caption"><h5><strong>3.</strong> <?php esc_html_e( 'Install the purchased product', 'wpscore_lang' ); ?></h5></div>
									</div>
								</div>
								<div class="col-xs-12 col-md-6">
									<div class="thumbnail">
										<img src="<?php echo esc_url( WPSCORE_URL ); ?>admin/assets/images/product-connection-step-4.jpg">
										<div class="caption"><h5><strong>4.</strong> <?php esc_html_e( 'Activate the purchased product', 'wpscore_lang' ); ?></h5></div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
			<!-- /Create Connection Infos Modal -->

			<!-- Create Requirements Infos Modal -->
			<div class="modal fade" id="requirements-modal">
				<div class="modal-dialog" role="document">
					<div class="modal-content">
						<div class="modal-header">
							<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only"><?php esc_html_e( 'Close', 'wpscore_lang' ); ?></span></button>
							<h4/ class="modal-title text-center"><?php esc_html_e( 'Requirements for', 'wpscore_lang' ); ?> {{currentProduct.infos.title}}</h4>
						</div>
						<div class="modal-body">
							<div v-if="currentProduct.infos.requirements == ''" class="alert alert-success text-center">
								<p><?php esc_html_e( 'There is no requirement to use this product. This product will work properly.', 'wpscore_lang' ); ?></p>
							</div>
							<template v-else>
								<p class="text-center"><?php esc_html_e( 'These following PHP elements must be installed on your server to use this product', 'wpscore_lang' ); ?></p>
								<table class="table table-bordered table-striped">
									<tr>
										<th><?php esc_html_e( 'Name', 'wpscore_lang' ); ?></th>
										<th><?php esc_html_e( 'Type', 'wpscore_lang' ); ?></th>
										<th><?php esc_html_e( 'Installed', 'wpscore_lang' ); ?></th>
									</tr>
									<tr v-for="requirement in currentProduct.infos.requirements">
										<td>
											<strong>{{requirement.name}}</strong>
										</td>
										<td>
											PHP {{requirement.type}}
										</td>
										<td>
											<span v-if="requirement.status" class="text-success">
												<i class="fa fa-check" aria-hidden="true"></i> <?php esc_html_e( 'yes', 'wpscore_lang' ); ?>
											</span>
											<span v-else  class="text-danger">
												<i class="fa fa-times" aria-hidden="true"></i> <?php esc_html_e( 'no', 'wpscore_lang' ); ?>
											</span>
										</td>
									</tr>
								</table>
								<div v-if="currentProduct.isAllRequirementsOk" class="alert alert-success text-center">
									<p><?php esc_html_e( 'All required PHP elements are installed on your server. This product will work properly.', 'wpscore_lang' ); ?></p>
								</div>
								<div v-else class="alert alert-danger text-center">
									<p><?php esc_html_e( 'Some PHP elements are not installed on your server. This product may not work properly. Please contact your web hoster.', 'wpscore_lang' ); ?></p>
								</div>
							</template>
						</div>
					</div>
				</div>
			</div>
			<!-- /Create Requirements Infos Modal -->

			<!-- Create Connection Infos Modal -->
			<div class="modal fade" id="install-modal">
				<div class="modal-dialog" role="document">
					<div class="modal-content">
						<div class="modal-header">
							<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only"><?php esc_html_e( 'Close', 'wpscore_lang' ); ?></span></button>
							<h4 class="modal-title text-center"><?php esc_html_e( 'An error occured while installing or updating', 'wpscore_lang' ); ?></h4>
						</div>
						<div class="modal-body">
							<div class="row">
								<div class="col-xs-12">
									<div class="alert alert-danger text-center">
										<?php esc_html_e( 'Your server configuration prevents the product to be installed automatically.', 'wpscore_lang' ); ?>
									</div>
									<template v-if="!installModal.showMoreInfos">
										<p class="text-center">
											<a href="#" @click.prevent="installModal.showMoreInfos = true"><?php esc_html_e( 'Show more infos', 'wpscore_lang' ); ?></a>
										</p>
									</template>
									<template v-else>
										<p class="text-center">
											<a href="#" @click.prevent="installModal.showMoreInfos = false"><?php esc_html_e( 'Hide more infos', 'wpscore_lang' ); ?></a>
										</p>
										<div class="panel panel-default">
											<div class="panel-body">
												{{installModal.message}}
											</div>
										</div>
									</template>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
			<!-- /Create Connection Infos Modal -->
		</div>
	</div>
	<?php
}
