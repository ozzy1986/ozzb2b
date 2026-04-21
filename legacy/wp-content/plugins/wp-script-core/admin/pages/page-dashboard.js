//jetpack fix
_.contains = _.includes;
window.lodash = _.noConflict();

window.onload = function () {
  if (document.getElementById("dashboard")) {
    /**
     * Add i18n globaly for translations
     */
    Vue.prototype.$i18n = WPSCORE_dashboard.i18n;

    /**
     * Add Event Bus
     */
    var EventBus = new Vue();

    /**
     * Add components
     */

    /** Product component */
    var wpsVueProduct = {

      // Product component name
      name: 'product',

      // Product component props
      props: [
        "productType",
        "productFromApi",
        "installedProduct",
        "userLicense",
        "wpsGoldSiteConnected"
      ],

      // Product component data
      data: function () {
        return {
          loading: {
            connect: false,
            install: false,
            toggle: false
          },
          showPopOver: false,
          currentUrl: window.location.hostname
        };
      },

      // Product component computed data
      computed: {
        autoConnect: function () {
          return "?ac=" + Base64.encode(this.userLicense);
        },
        bgGradient: function () {
          if( !this.productFromApi.bg_color_start || !this.productFromApi.bg_color_start ) return false;
          var opacity = 1;

          var rgb = {
            start: hexToRgb(this.productFromApi.bg_color_start),
            end: hexToRgb(this.productFromApi.bg_color_end)
          }
          var rgba = {
            start: [rgb.start.r, rgb.start.g, rgb.start.b, opacity],
            end: [rgb.end.r, rgb.end.g, rgb.end.b, opacity]
          }
          return "background: linear-gradient( 135deg, rgba(" + rgba.end.join(",") + ") 50%, rgba(" + rgba.start.join(",") + ") 100% );"
        },
        bgImage: function () {
          if (this.productType === 'theme' && this.productFromApi.preview_url) {
            var bgUrl = this.productFromApi.preview_url.replace('.png', '-530x150.jpg');
            return "background-image: url(" + bgUrl + ");";
          }
          return false;
        },
        productIs: function () {
          return {
            activated: lodash.has(this.installedProduct, "state") && this.installedProduct.state == "activated",
            connected: this.productFromApi.status == "connected",
            debug: this.productFromApi.debug,
            adult: this.productFromApi.adult_product,
            freemium: this.productFromApi.model == "freemium",
            installed: this.installedProduct !== undefined,
            updatable: lodash.has(this.installedProduct, "installed_version") && versionCompare(this.productFromApi.latest_version, this.installedProduct.installed_version) > 0,
          };
        },
        isAllRequirementsOk: function () {
          var output = true;
          lodash.each(this.productFromApi.requirements, function(r) {
            if (r.status === false) output = false;
          });
          return output;
        },
        plus18Icon: function () {
          return '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Capa_1" x="0px" y="0px" viewBox="0 0 328.863 328.863" style="enable-background:new 0 0 328.863 328.863;" xml:space="preserve" width="25" height="25" src="https://www.easyvideosite.com/wp-content/themes/wps/img/plus-18.svg"><g id="_x34_4-18Plus_movie"><g><path class="wps-plus-18" d="M104.032,220.434V131.15H83.392V108.27h49.121v112.164H104.032z" fill="#cf48cf"></path></g><g><path class="wps-plus-18" d="M239.552,137.23c0,9.76-5.28,18.4-14.08,23.201c12.319,5.119,20,15.84,20,28.32c0,20.16-17.921,32.961-45.921,32.961    c-28.001,0-45.921-12.641-45.921-32.48c0-12.801,8.32-23.682,21.28-28.801c-9.44-5.281-15.52-14.24-15.52-24 c0-17.922,15.681-29.281,40.001-29.281C224.031,107.15,239.552,118.83,239.552,137.23z M180.51,186.352 c0,9.441,6.721,14.721,19.041,14.721c12.32,0,19.2-5.119,19.2-14.721c0-9.279-6.88-14.561-19.2-14.561 C187.23,171.791,180.51,177.072,180.51,186.352z M183.391,138.83c0,8.002,5.76,12.48,16.16,12.48c10.4,0,16.16-4.479,16.16-12.48 c0-8.318-5.76-12.959-16.16-12.959C189.15,125.871,183.391,130.512,183.391,138.83z" fill="#cf48cf"></path></g><g><path class="wps-plus-18" d="M292.864,120.932c4.735,13.975,7.137,28.592,7.137,43.5c0,74.752-60.816,135.568-135.569,135.568 S28.862,239.184,28.862,164.432c0-74.754,60.816-135.568,135.569-135.568c14.91,0,29.527,2.4,43.5,7.137V5.832 C193.817,1.963,179.24,0,164.432,0C73.765,0,0.001,73.764,0.001,164.432s73.764,164.432,164.431,164.432 S328.862,255.1,328.862,164.432c0-14.807-1.962-29.385-5.831-43.5H292.864z" fill="#cf48cf"></path></g><g><polygon class="wps-plus-18" points="284.659,44.111 284.659,12.582 261.987,12.582 261.987,44.111 230.647,44.111 230.647,66.781 261.987,66.781  261.987,98.309 284.659,98.309 284.659,66.781 316.186,66.781 316.186,44.111" fill="#cf48cf"></polygon></g></g></svg>';
        }
      },

      // Product component methods
      methods: {
        choosePlan: function (plan) {
          this.plan = plan;
        },
        togglePopOver: function () {
          this.showPopOver = !this.showPopOver;
        },
        connectProduct: function () {
          this.loading.connect = true;
          this.$http
            .post(
              WPSCORE_dashboard.ajax.url,
              {
                action: "wpscore_connect_product",
                nonce: WPSCORE_dashboard.ajax.nonce,
                product_type: this.productType + 's',
                product_sku: this.productFromApi.sku,
                product_title: this.productFromApi.title
              },
              {
                emulateJSON: true
              }
            )
            .then(
              function (response) {
                // success callback
                if (response.body.code == "error") {
                  console.error(response.body.message);
                } else {
                  this.loading.connect = this.$i18n['loading_reloading'];
                  document.location.href = "admin.php?page=wpscore-dashboard";
                }
              },
              function (error) {
                // error callback
                console.error(error);
              }
            )
            .then(function () {});
        },
        installProduct: function (method) {
          this.loading.install = true;
          this.$http
            .post(
              WPSCORE_dashboard.ajax.url,
              {
                action: "wpscore_install_product",
                nonce: WPSCORE_dashboard.ajax.nonce,
                product_sku: this.productFromApi.sku,
                product_type: this.productType,
                product_zip: this.productFromApi.zip_file,
                product_slug: this.productFromApi.slug,
                product_folder_slug: this.productFromApi.folder_slug,
                method: method,
                new_version: this.productFromApi.latest_version
              },
              {
                emulateJSON: true
              }
            )
            .then(
              function (response) {
                // installProduct success callback
                if (response.body === true || response.body == '<div class="wrap"><h1></h1></div>') {
                  this.loading.toggle = this.$i18n['loading_reloading'];
                  document.location.href = "admin.php?page=wpscore-dashboard";
                } else {
                  this.showInstallModal(response.body);
                }
              },
              function (error) {
                // installProduct error callback
                console.error(error);
              }
            )
            .then( function () {
              this.loading.install = false;
            });
        },
        toggleProduct: function () {
          this.loading.toggle = true;
          this.$http
            .post(
              WPSCORE_dashboard.ajax.url,
              {
                action: "wpscore_toggle_" + this.productType,
                nonce: WPSCORE_dashboard.ajax.nonce,
                product_folder_slug: this.productFromApi.folder_slug
              },
              {
                emulateJSON: true
              }
            )
            .then(
              function (response) {
                // toggleProduct success callback
                if (lodash.has(this.installedProduct, "state")) {
                  this.installedProduct.state = response.body.product_state;
                }
              },
              function (error) {
                // toggleProduct error callback
                console.error(error);
              }
            )
            .then( (function () {
              this.loading.toggle = 'reloading';
              if (this.installedProduct.state == "activated") {
                document.location.href = "admin.php?page=wpscore-dashboard&activated=true";
              } else {
                document.location.href = "admin.php?page=wpscore-dashboard";
              }
            }).bind(this));
        },
        showRequirementsModal: function (productInfos, isAllRequirementsOk) {
          EventBus.$emit("show-requirements-modal", productInfos, isAllRequirementsOk);
        },
        showInstallModal: function (productInfos) {
          EventBus.$emit("show-install-modal", productInfos);
        },
        showConnectionInfosModal: function () {
          EventBus.$emit("show-connection-infos-modal");
        }
      },

      // Product component template
      template: `
        <div class="product" v-bind:class="{'product__connected' : productIs.connected, 'product__plugin' : productType == 'plugin', 'product__theme' : productType == 'theme'}">
          <div class="product__gradient" v-bind:style="bgGradient"></div>
          <div class="product__image" v-bind:style="bgImage"></div>
          <div class="product__logo"><img v-bind:src="productFromApi.icon_url"></div>
          <div class="product__description">
            <div class="product__requirements" v-on:click="showRequirementsModal(productFromApi, isAllRequirementsOk)">
              <small>{{$i18n['product__requirements']}} <i class="fa" v-bind:class="[isAllRequirementsOk ? 'fa-check text-success' : 'fa-exclamation-triangle text-danger']" aria-hidden="true"></i></small>
            </div>

            <div v-if="!wpsGoldSiteConnected" v-on:click="showConnectionInfosModal" v-bind:class="[productIs.connected ? 'text-success' : 'text-danger']" class="product__connection text-success">
              <small><i class="fa fa-circle" aria-hidden="true"></i> <span v-if="productIs.connected">{{$i18n['product__connected']}}</span><span v-else>{{$i18n['product__notConnected']}}</span></small>
            </div>

              <h4 class="product__title">{{productFromApi.title}} <span v-if="productIs.adult" v-html="plus18Icon" class="product__adult-icon"></span></h4>
              <div class="product__installed">
                <span v-if="productIs.installed" class="product__version-installed">
                  v{{installedProduct.installed_version}} {{$i18n['product__version-installed']}}
                </span>
                <span v-else class="product__not-installed">
                  {{$i18n['product__not-installed']}}
                </span>
              </div>
              <p class="product__exerpt">{{productFromApi.exerpt}} <span class="product__learn-more">&mdash; <a v-bind:href="'https://www.wp-script.com/' + productType + 's/' + productFromApi.slug + '/?utm_source=core&utm_medium=dashboard&utm_campaign=' + productFromApi.slug + '&utm_content=learnMore'" target="_blank" v-bind:title="'View details about ' + productFromApi.title">Learn more</a></span></p>
          </div>

          <div class="product__footer">
            <template v-if="!productIs.installed && (productIs.connected || productIs.freemium)">
              <button v-if="!loading.toggle && !loading.install" v-on:click.prevent="installProduct('install')" class="btn btn-sm btn-default" v-bind:title="'Install ' + productFromApi.title"><i class="fa fa-download" aria-hidden="true"></i> {{$i18n['product__footer__install']}}</button>
              <button v-if="!loading.toggle && loading.install" class="btn btn-sm btn-default disabled" disabled v-bind:title="'Installing ' + productFromApi.title"><i class="fa fa-cog fa-spin fa-fw" aria-hidden="true"></i> {{$i18n['product__footer__installing']}}...</button>
              <button v-if="loading.toggle == true" class="btn btn-sm btn-default disabled" disabled v-bind:title="'Activating ' + productFromApi.title"><i class="fa fa-cog fa-spin fa-fw" aria-hidden="true"></i> {{$i18n['product__footer__activating']}}...</button>
              <button v-if="loading.toggle == 'reloading'" class="btn btn-sm btn-default disabled" disabled v-bind:title="'Reloading'" target="_blank"><i class="fa fa-cog fa-spin-reverse fa-fw" aria-hidden="true"></i> {{$i18n['product__footer__reloading']}}...</button>
            </template>

            <template v-if="!productIs.connected">
              <template v-if="productFromApi.connectable_sites >= 1 || productFromApi.connectable_sites == 'unlimited'">
                <button v-on:click.prevent="togglePopOver" class="btn btn-sm btn-success" v-bind:title="'Connect ' + productFromApi.title + ' on this domain'" target="_blank"><i class="fa fa-plus-circle" aria-hidden="true"></i> Connect &nbsp;<i class="fa fa-caret-down" aria-hidden="true"></i></button>
              </template>
              <template v-else>
                <a v-bind:href="'https://www.wp-script.com/' + productType + 's/' + productFromApi.slug + '/' + autoConnect + '&utm_source=core&utm_medium=dashboard&utm_campaign=' + productFromApi.slug + '&utm_content=buyNow'" target="_blank"  class="btn btn-sm btn-pink" v-bind:title="'Buy ' + productFromApi.title">
                  <i class="fa fa-shopping-cart"></i>&nbsp;
                  {{$i18n['product__footer__purchase']}}
                </a>
              </template>
            </template>
            <template v-if="productIs.connected && productIs.installed">
                <transition name="wps-anim__y-up" mode="out-in" key="reloading">
                  <span v-if="loading.toggle == 'reloading'"><i class="fa fa-cog fa-spin-reverse fa-fw"></i> {{$i18n['product__footer__reloading']}}...</span>
                  <span v-else key="not-reloading">
                    <template v-if="productIs.updatable">
                      <button v-if="!loading.install" class="btn btn-sm btn-success" href="#" v-on:click.prevent="installProduct('upgrade')"><i aria-hidden="true" class="fa fa-refresh"></i> {{$i18n['product__footer__updateTo']}} v{{productFromApi.latest_version}}</button>
                      <button v-else class="btn btn-sm btn-success disabled" disabled href="#"><i aria-hidden="true" class="fa fa-cog fa-spin fa-fw"></i> {{$i18n['product__footer__updatingTo']}} v{{productFromApi.latest_version}}...</button>
                    </template>
                    <template v-if="installedProduct.state == 'deactivated'">
                        <span v-if="loading.toggle == false"><a class="btn btn-sm btn-default product__btn--activate" href="#" v-on:click.prevent="toggleProduct">{{$i18n['product__footer__activate']}}</a></span>
                        <span v-else><i class="fa fa-cog fa-spin fa-fw"></i> {{$i18n['product__footer__activating']}}...</span>
                    </template>
                    <template v-if="installedProduct.state == 'activated'">
                      <template v-if="productType == 'plugin'">
                          <span v-if="loading.toggle == false"><a class="btn btn-sm btn-default product__btn--deactivate" href="#" v-on:click.prevent="toggleProduct">{{$i18n['product__footer__deactivate']}}</a></span>
                          <span v-else><i class="fa fa-cog fa-spin fa-fw"></i> {{$i18n['product__footer__deactivating']}}...</span>
                      </template>
                      <template v-else>{{$i18n['product__footer__active_theme']}}</template>
                    </template>
                  </span>
                </transition>
            </template>
          </div>

          <div class="product__over" v-bind:class="{'show product__over--show':showPopOver}">
            <template v-if="productIs.connected && !productIs.installed">
              <p class="product__over-p">Install {{productFromApi.title}} to use it</p>
            </template>

            <template v-if="!productIs.connected">
              <template v-if="productFromApi.connectable_sites >= 1 || productFromApi.connectable_sites == 'unlimited'">
                <p class="product__over-p">Connect <strong>{{productFromApi.title}}</strong> on <span class="product__over-domain">{{currentUrl}}</span>
                <template v-if="productFromApi.connectable_sites !== 'unlimited'"><br><small>Connecting will decrease your sites left by 1</small></template>
                <br><span class="text-success">Sites left: <strong>{{productFromApi.connectable_sites}}</strong></span></p>
                <div class="product__footer">
                  <button v-on:click.prevent="togglePopOver" class="btn btn-sm btn-default mr-2"><i class="fa fa-times" aria-hidden="true"></i> Close</button>
                  <button  v-if="loading.connect == false" v-on:click.prevent="connectProduct" class="btn btn-sm btn-success" v-bind:title="'Connect ' + productFromApi.title + ' on this domain'" target="_blank"><i class="fa fa-plus-circle" aria-hidden="true"></i> Connect now</button>
                  <button v-else class="btn btn-sm btn-success disabled" disabled v-bind:title="'Connecting ' + productFromApi.title + ' on this domain'" target="_blank"><i class="fa fa-cog fa-spin fa-fw" aria-hidden="true"></i> Connecting...</button>
                </div>
              </template>
            </template>
          </div>
        </div>
      `,
    };

    /** Products component */
    var wpsVueProducts = {

      // Products component name
      name: 'products',

      // Products component use those components
      components: {
        'product': wpsVueProduct
      },

      // Products component filters
      filters: {
        titled(value) {
          return value.charAt(0).toUpperCase() + value.slice(1) + "s";
        }
      },

      // Products component props
      props: [
        "products",
        "type",
        "installedProducts",
        "userLicense",
        "wpsGoldSiteConnected"
      ],

      // Products component data
      data: function () {
        return {
          filter: "All"
        };
      },

      // Products component methods
      methods: {
        toggleFilter: function (newValue) {
          this.filter = this.$i18n['products__filter__' + newValue];
          lodash.each(this.products, (function (productFromApi) {
            var productSku = productFromApi.sku;
            switch (newValue) {
              case "all":
                productFromApi.show = true;
                break;
              case "connected":
                productFromApi.show = productFromApi.status == "connected";
                break;
              case "notConnected":
                productFromApi.show = productFromApi.status != "connected";
                break;
              case "installed":
                productFromApi.show = lodash.has(this.installedProducts, productSku);
                break;
              case "notInstalled":
                productFromApi.show = !lodash.has(this.installedProducts, productSku);
                break;
              default:
                productFromApi.show = false;
                break;
            }
          }).bind(this));
        },
      },

      // Products component template
      template: `
        <div class="row">
          <h3>{{type | titled}}
            <div class="btn-group">
              <button type="button" class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                {{filter}} <span class="caret"></span>
              </button>
              <ul class="dropdown-menu">
                <li><a href="#" v-on:click.prevent="toggleFilter('all')">{{$i18n['products__filter__all']}}</a></li>
                <li role="separator" class="divider"></li>
                <li><a href="#" v-on:click.prevent="toggleFilter('connected')">{{$i18n['products__filter__connected']}}</a></li>
                <li><a href="#" v-on:click.prevent="toggleFilter('notConnected')">{{$i18n['products__filter__notConnected']}}</a></li>
                <li role="separator" class="divider"></li>
                <li><a href="#" v-on:click.prevent="toggleFilter('installed')">{{$i18n['products__filter__installed']}}</a></li>
                <li><a href="#" v-on:click.prevent="toggleFilter('notInstalled')">{{$i18n['products__filter__notInstalled']}}</a></li>
              </ul>
            </div>
          </h3>
          <div class="products">
            <div v-for="product in products" class="col-xs-12 col-md-6 col-lg-4" v-bind:class="{'product__hidden' : ! product.show}">
              <product
                v-bind:key="product.sku"
                v-bind:product-type="type"
                v-bind:product-from-api="product"
                v-bind:installed-product="installedProducts[product.sku]"
                v-bind:user-license="userLicense"
                v-bind:wps-gold-site-connected="wpsGoldSiteConnected">
              </product>
            </div>
            <div class="clear"></div>
          </div>
        </div>
      `
    };

    /**
     * Create main Vue instance
     */
    var wpsVueDashboard = new Vue({

      // main instance el
      el: "#dashboard",

      // main instance uses those components
      components: {
        'products': wpsVueProducts
      },

      // main instance data
      data: {
        error: "",
        loading: {
          checkingAccount: false,
          checkingLicense: false,
          loadingData: false,
          updatingCore: false,
          connectingSite: false
        },
        dataLoaded: false,
        userID: 0,
        userLicense: "",
        userLicenseInput: "",
        userEmail: "",
        userEmailInput: "",
        productsFromApi: {},
        installedProducts: {},
        core: {},
        wpsGold: false,
        currentProduct: {
          infos: [],
          isAllRequirementsOk: false
        },
        installModal: {
          message: "",
          showMoreInfos: false
        }
      },
      computed: {
        toggleLicenseBtn: function () {
          return this.userLicenseInput.length == 0;
        },
        userLicenseChanged: function () {
          return this.userLicense !== this.userLicenseInput;
        },
        licenseButtonIconClass: function () {
          if (!this.userLicenseChanged) {
            return "fa-check text-success";
          } else if (this.loading.checkingLicense) {
            return "fa-cog fa-spin";
          } else if (this.error != "") {
            return "fa-times text-danger";
          } else {
            return "fa-refresh text-primary";
          }
        },
        licenceBoxClass: function () {
          if (this.loading.checkingLicense == this.$i18n['loading_reloading'])
            return "alert-success";
          if (this.error) return "alert-danger";
          return "alert-info";
        },
        wpsGoldSiteState: function () {
          var siteState = {
            paragraph: "",
            linkHref: "",
            buttonClass: "",
            buttonText: "",
            iconClass: ""
          };
          if (this.wpsGold.site_connected) return siteState;
          if (this.wpsGold.time_remaining <= 0) {
            if (this.wpsGold.current_plan) {
              siteState.buttonText = this.$i18n['gold__button_reactivate'];
              siteState.paragraph = this.$i18n['gold__subscription_expired'];
              siteState.linkHref = "https://www.wp-script.com/gold/?utm_source=core&utm_medium=dashboard&utm_campaign=gold&utm_content=reJoin";
              siteState.iconClass = ["fa", "fa-trophy"];
            } else {
              siteState.buttonText = this.$i18n['gold__button_join'];
              siteState.paragraph = this.$i18n['gold__subscription_join'];
              siteState.linkHref = "https://www.wp-script.com/gold/?utm_source=core&utm_medium=dashboard&utm_campaign=gold&utm_content=join";
              siteState.iconClass = ["fa", "fa-trophy"];
            }
          } else {
            if (this.wpsGold.sites_remaining > 0) {
              siteState.paragraph = this.$i18n['gold__subscription_connect'];
              switch (this.loading.connectingSite) {
                case false:
                  siteState.buttonText = "Connect this site";
                  siteState.iconClass = ["fa", "fa-plug"];
                  break;
                case true:
                  siteState.buttonText = "Connecting site";
                  siteState.iconClass = ["fa", "fa-cog", "fa-spin", "fa-fw"];
                  break;

                case $i18n['loading_reloading']:
                  siteState.buttonText = this.$i18n['loading_reloading'];
                  siteState.iconClass = ["fa", "fa-cog", "fa-spin-reverse", "fa-fw"];
                  break;
                default:
                  break;
              }
            } else {
              if (this.wpsGold.current_plan < 25) {
                siteState.buttonText = this.$i18n['gold__button_upgrade'];
                siteState.paragraph = this.$i18n['gold__subscription_limit-reached'] + '(' + this.wpsGold.current_plan + ')';
                siteState.linkHref = "https://www.wp-script.com/gold/?utm_source=core&utm_medium=dashboard&utm_campaign=gold&utm_content=upgrade";
                siteState.iconClass = ["fa", "fa-shopping-cart"];
              } else {
                siteState.buttonText = this.$i18n['gold__button_contact-us'];
                siteState.paragraph = this.$i18n['gold__subscription_limit-reached'] + '(' + this.wpsGold.current_plan + ')';
                siteState.linkHref = "https://www.wp-script.com/contact/?utm_source=core&utm_medium=gold&utm_campaign=gold&utm_content=25sitesReached";
                siteState.iconClass = ["fa", "fa-comments-o"];
              }
            }
          }
          return siteState;
        }
      },

      // main instance created hook
      created: function () {
        EventBus.$on("show-requirements-modal", (function (productInfos, isAllRequirementsOk) {
          this.currentProduct.infos = productInfos;
          this.currentProduct.isAllRequirementsOk = isAllRequirementsOk;
          jQuery("#requirements-modal").modal("show");
        }).bind(this));

        EventBus.$on("show-install-modal", (function (productInfos) {
          this.installModal.message = productInfos;
          jQuery("#install-modal").modal("show");
        }).bind(this));

        EventBus.$on("show-connection-infos-modal", (function () {
          jQuery("#connection-infos-modal").modal("show");
        }).bind(this));
      },

      // main instance mounted hook
      mounted: function () {
        this.loadData();
      },

      // main instance methods
      methods: {
        loadData: function () {
          this.loading.loadingData = true;
          this.$http
            .post(
              WPSCORE_dashboard.ajax.url,
              {
                action: "wpscore_load_dashboard_data",
                nonce: WPSCORE_dashboard.ajax.nonce
              },
              {
                emulateJSON: true
              }
            )
            .then(
              function (response) {
                // success callback
                this.userLicense = response.body.user_license;
                this.userLicenseInput = response.body.user_license;
                this.userEmail = this.userEmailInput = response.body.user_email;
                this.productsFromApi = response.body.products;
                this.core = response.body.core;
                this.wpsGold = response.body.wps_gold;

                lodash.each(this.productsFromApi, function (productsByType) {
                  lodash.each(productsByType, function (product) {
                    product.show = true;
                  });
                });
                this.installedProducts = response.body.installed_products;
              },
              function (error) {
                // error callback
                console.error(error);
              }
            )
            .then( function () {
              this.loading.loadingData = false;
              this.dataLoaded = true;
            });
        },

        checkLicense: function () {
          this.loading.checkingLicense = true;
          var savedLicenseInput = this.userLicense;
          this.$http
            .post(
              WPSCORE_dashboard.ajax.url,
              {
                action: "wpscore_check_license_key",
                nonce: WPSCORE_dashboard.ajax.nonce,
                license_key: this.userLicenseInput
              },
              {
                emulateJSON: true
              }
            )
            .then(
              function (response) {
                // success callback
                if (response.body.code === "success") {
                  this.userLicense = this.userLicenseInput;
                  this.loading.checkingLicense = this.$i18n['loading_reloading'];
                  document.location.href = "admin.php?page=wpscore-dashboard";
                } else if (response.body.code === "error") {
                  this.error = this.userLicenseInput = response.body.message;
                  setTimeout((function () {
                    this.userLicenseInput = savedLicenseInput;
                    this.error = "";
                    this.$refs.refLicenseInput.focus();
                  }).bind(this), 3000);
                } else {
                  this.error = this.userLicenseInput = this.$i18n['license__invalid'];
                  setTimeout((function () {
                    this.userLicenseInput = savedLicenseInput;
                    this.error = "";
                    this.$refs.refLicenseInput.focus();
                  }).bind(this), 3000);
                }
              },
              function (error) {
                // error callback
                console.error(error);
              }
            )
            .then( function () {
              this.loading.checkingLicense = false;
            });
        },

        checkAccount: function () {
          this.loading.checkingAccount = true;
          var savedEmailInput = this.userEmail;
          this.$http
            .post(
              WPSCORE_dashboard.ajax.url,
              {
                action: "wpscore_check_account",
                nonce: WPSCORE_dashboard.ajax.nonce,
                email: this.userEmailInput
              },
              {
                emulateJSON: true
              }
            )
            .then(
              function (response) {
                // success callback
                if (response.body.code === "success") {
                  this.loading.checkingAccount = this.$i18n['loading_reloading'];
                  this.loading.checkingLicense = this.$i18n['loading_reloading'];
                  this.userLicense = this.userLicenseInput = response.body.data.license;
                  setTimeout(function () {
                    document.location.href = "admin.php?page=wpscore-dashboard";
                  }, 3000);
                } else if (response.body.code === "error") {
                  this.error = this.userEmailInput = response.body.message;
                  setTimeout((function () {
                    this.userEmailInput = savedEmailInput;
                    this.error = "";
                    this.$refs.refEmailInput.focus();
                    this.loading.checkingAccount = false;
                  }).bind(this), 3000);
                } else {
                  this.error = this.userEmailInput = this.$i18n['license__invalid'];
                  setTimeout((function () {
                    this.userEmailInput = savedEmailInput;
                    this.$refs.refEmailInput.focus();
                    this.loading.checkingAccount = false;
                  }).bind(this), 3000);
                }
              },
              function (error) {
                // error callback
                console.error(error)
              }
            )
            .then( function () {});
        },

        updateCore: function () {
          this.loading.updatingCore = true;
          this.$http
            .post(
              WPSCORE_dashboard.ajax.url,
              {
                action: "wpscore_install_product",
                nonce: WPSCORE_dashboard.ajax.nonce,
                product_sku: this.core.sku,
                product_type: "plugin",
                product_zip: this.core.zip_file,
                product_slug: this.core.slug,
                product_folder_slug: this.core.folder_slug,
                method: "upgrade",
                new_version: this.core.latest_version
              },
              {
                emulateJSON: true
              }
            )
            .then(
              function (response) {
                // success callback
                if (
                  response.body === true ||
                  response.body == '<div class="wrap"><h1></h1></div>'
                ) {
                  this.loading.updatingCore = this.$i18n['loading_reloading'];
                  document.location.href = "admin.php?page=wpscore-dashboard";
                } else {
                  this.showInstallModal(response.body);
                }
              },
              function (error) {
                // error callback
                console.error(error);
              }
            )
            .then( function () {});
        },

        wpsGoldConnectSite: function () {
          this.loading.connectingSite = true;
          this.$http
            .post(
              WPSCORE_dashboard.ajax.url,
              {
                action: "wpscore_wpsgold_connect_site",
                nonce: WPSCORE_dashboard.ajax.nonce
              },
              {
                emulateJSON: true
              }
            )
            .then(
              function (response) {
                // success callback
                if (response.body.code == "error") {
                  console.error(response.body.message);
                } else {
                  this.loading.connectingSite = this.$i18n['loading_reloading'];
                  document.location.href = "admin.php?page=wpscore-dashboard";
                }
              },
              function (error) {
                // error callback
                console.error(error);
              }
            )
            .then( function () {
              this.connectSite = false;
            });
        },

        toggleFilter: function (productType, newValue) {
          this.filters[productType] = newValue;
          lodash.each(this.productsFromApi[productType], function (productFromApi) {
            var productSku = productFromApi.sku;
            switch (newValue) {
              case "All":
                productFromApi.show = true;
                break;
              case "Connected":
                productFromApi.show = productFromApi.status == "connected";
                break;
              case "Not connected":
                productFromApi.show = productFromApi.status != "connected";
                break;
              case "Installed":
                productFromApi.show = this.installedProduct !== undefined;
                break;
              case "Not installed":
                productFromApi.show = this.installedProduct === undefined;
                break;
              case "Activated":
                productFromApi.show = lodash.has(this.installedProducts[productType][productSku], "state") && this.installedProducts[productType][productSku].state == "activated";
                break;
              case "Not activated":
                productFromApi.show = !lodash.has(this.installedProducts[productType][productSku], "state") || (lodash.has(this.installedProducts[productType][productSku], "state") && this.installedProducts[productType][productSku].state != "activated");
                break;
              default:
                productFromApi.show = false;
                break;
            }
          });
        }
      }
    });
  }
};

// helper functions
function hexToRgb(hex) {
  var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
  } : null;
}

function versionCompare (a, b) {
  var i, diff;
  var regExStrip0 = /(\.0+)+$/;
  var segmentsA = a.replace(regExStrip0, '').split('.');
  var segmentsB = b.replace(regExStrip0, '').split('.');
  var l = Math.min(segmentsA.length, segmentsB.length);
  for (i = 0; i < l; i++) {
      diff = parseInt(segmentsA[i], 10) - parseInt(segmentsB[i], 10);
      if (diff) {
          return diff;
      }
  }
  return segmentsA.length - segmentsB.length;
}

var Base64 = {_keyStr:"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",encode:function(r){var t,e,o,a,h,n,c,d="",C=0;for(r=Base64._utf8_encode(r);C<r.length;)a=(t=r.charCodeAt(C++))>>2,h=(3&t)<<4|(e=r.charCodeAt(C++))>>4,n=(15&e)<<2|(o=r.charCodeAt(C++))>>6,c=63&o,isNaN(e)?n=c=64:isNaN(o)&&(c=64),d=d+this._keyStr.charAt(a)+this._keyStr.charAt(h)+this._keyStr.charAt(n)+this._keyStr.charAt(c);return d},decode:function(r){var t,e,o,a,h,n,c="",d=0;for(r=r.replace(/[^A-Za-z0-9+\/=]/g,"");d<r.length;)t=this._keyStr.indexOf(r.charAt(d++))<<2|(a=this._keyStr.indexOf(r.charAt(d++)))>>4,e=(15&a)<<4|(h=this._keyStr.indexOf(r.charAt(d++)))>>2,o=(3&h)<<6|(n=this._keyStr.indexOf(r.charAt(d++))),c+=String.fromCharCode(t),64!=h&&(c+=String.fromCharCode(e)),64!=n&&(c+=String.fromCharCode(o));return c=Base64._utf8_decode(c)},_utf8_encode:function(r){r=r.replace(/rn/g,"n");for(var t="",e=0;e<r.length;e++){var o=r.charCodeAt(e);o<128?t+=String.fromCharCode(o):o>127&&o<2048?(t+=String.fromCharCode(o>>6|192),t+=String.fromCharCode(63&o|128)):(t+=String.fromCharCode(o>>12|224),t+=String.fromCharCode(o>>6&63|128),t+=String.fromCharCode(63&o|128))}return t},_utf8_decode:function(r){for(var t="",e=0,o=c1=c2=0;e<r.length;)(o=r.charCodeAt(e))<128?(t+=String.fromCharCode(o),e++):o>191&&o<224?(c2=r.charCodeAt(e+1),t+=String.fromCharCode((31&o)<<6|63&c2),e+=2):(c2=r.charCodeAt(e+1),c3=r.charCodeAt(e+2),t+=String.fromCharCode((15&o)<<12|(63&c2)<<6|63&c3),e+=3);return t}};
