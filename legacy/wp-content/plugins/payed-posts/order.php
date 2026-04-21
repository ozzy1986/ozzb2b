<?php



// creates order for payed post

function create_order_payed_post( $draft_id, $post_type = 'post' ) {

	// default values for order

	$first_name	= 'Anonymous';

	$last_name	= '';

	$company	= '';

	$email		= 'no@email.here';

	$phone		= '';

	$address_1	= '';

	$address_2	= '';

	$city		= '';

	$state		= '';

	$postcode	= '';

	$country	= '';



	// if current user is logged in then use hid info

	$current_user = wp_get_current_user();

	if ( $current_user->ID ) {

		$user_data		= get_userdata( $current_user->ID );

		$user_meta		= get_user_meta( $current_user->ID );

		$wc_customer	= WC()->customer;

		

		if ( $user_meta['first_name'][0] ) {

			$first_name = $user_meta['first_name'][0];

		}

		if ( $user_meta['last_name'][0] ) {

			$last_name = $user_meta['last_name'][0];

		}

		if ( $user_data->data->user_email ) {

			$email = $user_data->data->user_email;

		}

		if ( $wc_customer->get_billing_company() ) {

			$company = $wc_customer->get_billing_company();

		}

		if ( $wc_customer->get_billing_company() ) {

			$company = $wc_customer->get_billing_company();

		}

		if ( $wc_customer->get_billing_phone() ) {

			$phone = $wc_customer->get_billing_phone();

		}

		if ( $wc_customer->get_billing_address_1() ) {

			$address_1 = $wc_customer->get_billing_address_1();

		}

		if ( $wc_customer->get_billing_address_2() ) {

			$address_2 = $wc_customer->get_billing_address_2();

		}

		if ( $wc_customer->get_billing_city() ) {

			$city = $wc_customer->get_billing_city();

		}

		if ( $wc_customer->get_billing_state() ) {

			$state = $wc_customer->get_billing_state();

		}

		if ( $wc_customer->get_billing_postcode() ) {

			$postcode = $wc_customer->get_billing_postcode();

		}

		if ( $wc_customer->get_billing_country() ) {

			$country = $wc_customer->get_billing_country();

		}

	}

	

	$address = array(

        'first_name' => $first_name,

        'last_name'  => $last_name,

        'company'    => $company,

        'email'      => $email,

        'phone'      => $phone,

        'address_1'  => $address_1,

        'address_2'  => $address_2, 

        'city'       => $city,

        'state'      => $state,

        'postcode'   => $postcode,

        'country'    => $country

    );



    // get durcoin payment method

    $available_gateways = WC()->payment_gateways->get_available_payment_gateways();

	if ( empty( $available_gateways['woodurcoin'] ) ) {

		wp_die( __( 'Durcoin payment method not found.', 'payed-posts' ) );

	}

	$durcoin_method = $available_gateways['woodurcoin'];

	//echo "\n " . ' <br>available_gateways:<pre> ' . print_r( $available_gateways, true ) . ' </pre><br> ' . " \n";

    

    $order = wc_create_order(); // create order

    

    // set user info

    $order->set_address( $address, 'billing' );

    $order->set_address( $address, 'shipping' );



    // set post draft in meta

    $order->update_meta_data( '_payed_post_id', $draft_id );
    $order->update_meta_data( '_payed_post_type', $post_type );



    if ( $post_type == 'comment' ) {

	    // add payed comment technical product

	    $payed_post_product = get_posts([ 

			'name'				=> 'payed_comment_technical_product', 

			'post_type'			=> 'product',

			'post_status'		=> 'publish',

			'posts_per_page'	=> 1

		]);

	} else {

		// add payed post technical product

	    $payed_post_product = get_posts([ 

			'name'				=> 'payed_post_technical_product', 

			'post_type'			=> 'product',

			'post_status'		=> 'publish',

			'posts_per_page'	=> 1

		]);

	}

    if ( $payed_post_product[0]->ID ) {

    	$order->add_product( wc_get_product( $payed_post_product[0]->ID ), 1 );

    } else {

    	wp_die( __( 'Technical payed post product not found.', 'payed-posts' ) );

    }



    // update order total

    $order->calculate_totals();



    // set payment method

    update_post_meta( $order->get_id(), '_payment_method', 'woodurcoin' );

    update_post_meta( $order->get_id(), '_payment_method_title', $durcoin_method->method_title );



    // Store Order ID in session so it can be re-used after payment failure

    WC()->session->order_awaiting_payment = $order->get_id();



    // Process Payment

    $result = $durcoin_method->process_payment( $order->get_id() );



    return $result;

}





// redirect user from order payment page to payment gateway page outside

add_action( 'wp_head', 'dpp_redirect_from_durcoin_payment_to_waves' );

function dpp_redirect_from_durcoin_payment_to_waves() {

	global $wp;



	// get page id of checkout page

	$checkout_id = wc_get_page_id('checkout');


	// check if current page is order payment page

	if ( @$wp->query_vars['order-pay'] > 0 and // we have order id and it is payment page
		( @$wp->query_vars['page_id'] == $checkout_id or @$wp->query_vars['pagename'] == 'checkout' ) // it is checout page
	) {

		// get current order

		$order_id = $wp->query_vars['order-pay']; // The order ID

	    $order    = wc_get_order( $order_id ); // Get the WC_Order Object instance



	    // check if current method is durcoin

	    $payment_method = $order->get_payment_method();

		//echo "\n " . ' <br>payment_method:<pre> ' . print_r( $payment_method, true ) . ' </pre><br> ' . " \n";

		if ( $payment_method != 'woodurcoin' ) {

			return false;

		}



		// redirect user straight to waves

		?>

		<script>

			jQuery(document).ready(function($) {

				// find durcoin button

				const button = $('a[href$="woodurcoin-pay-order-<?php echo $order_id;?>"]');

				if (button.length) {

					window.location.href = button.attr('href');

				}

			});

		</script>

		<?php



	} else {

		return false;

	}



}



// on successful payment page confirmation publish the user's post

add_action( 'wp', 'dpp_confirm_payment_and_publish_post' );

function dpp_confirm_payment_and_publish_post() {

	global $wp;

	

	//if ( is_order_received_page() ) {
	//if ( @$_GET['test'] == 'pay' ) {
	//	echo "\n " . ' <br>@$wp->query_vars:<pre> ' . print_r( @$wp->query_vars, true ) . ' </pre><br> ' . " \n";
	//}
	// check if current page is order received page

	if ( is_order_received_page() and @$wp->query_vars['order-received'] > 0 ) {

		// get current order

		$order_id = $wp->query_vars['order-received']; // The order ID

	    $order    = wc_get_order( $order_id ); // Get the WC_Order Object instance



	    // get payed post draft id

	    $draft_id	=  $order->get_meta( '_payed_post_id' );
	    $post_type	=  $order->get_meta( '_payed_post_type' );

	    if ( empty( $draft_id ) ) {

	    	return false;

	    }



	    // check if current method is durcoin

	    $payment_method = $order->get_payment_method();

		//echo "\n " . ' <br>payment_method:<pre> ' . print_r( $payment_method, true ) . ' </pre><br> ' . " \n";

		if ( $payment_method != 'woodurcoin' ) {

			return false;

		}



		// finally publish post or approve comment

		if ( $post_type == 'comment' ) {

			wp_set_comment_status( $draft_id, 'approve' );

			$post_url = get_comment_link( $draft_id );

		} else {

			$update_result = wp_update_post([

				'ID'			=> $draft_id,

				'post_status'	=> 'publish'

			]);

			$post_url = get_permalink( $draft_id );

		}



		// and redirect user to this post

		if ( $post_url ) {

			header( 'Location: ' . $post_url );

			exit;

		}



	} else {

		return false;

	}



}