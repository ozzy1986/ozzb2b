<?php

// create product that represents payed post publication
function dpp_create_payed_post_product() {
	// check if product exists first
	$existing_product = get_posts([ 
		'name'				=> 'payed_post_technical_product', 
		'post_type'			=> 'product',
		'post_status'		=> 'publish',
		'posts_per_page'	=> 1
	]);
	//echo "\n " . ' <br>existing_product:<pre> ' . print_r( $existing_product, true ) . ' </pre><br> ' . " \n";

	if ( !empty( $existing_product ) ) {
		return true;
	}

	//Woocommerce CRUD
	$obj_product = new WC_Product_Simple();

	$obj_product->set_name('payed_post_technical_product'); //Set product name.
	$obj_product->set_status('publish'); //Set product status.
	$obj_product->set_virtual(true);
	$obj_product->set_catalog_visibility('hidden'); //Set catalog visibility.	| string $visibility Options: 'hidden', 'visible', 'search' and 'catalog'.
	$obj_product->set_description( __( 'This is technical product (for post) which is not displayed on front-end. It is only required so that Payed Posts can work.', 'payed-posts' ) ); //Set product description.
	$obj_product->set_sold_individually(true); //Set if should be sold individually.            | bool
	$obj_product->set_reviews_allowed(false); //Set if reviews is allowed.                        | bool

	$new_product_id = $obj_product->save(); //Saving the data to create new product, it will return product ID.
}

// create product that represents payed post publication
function dpp_create_payed_comment_product() {
	// check if product exists first
	$existing_product = get_posts([ 
		'name'				=> 'payed_comment_technical_product', 
		'post_type'			=> 'product',
		'post_status'		=> 'publish',
		'posts_per_page'	=> 1
	]);
	//echo "\n " . ' <br>existing_product:<pre> ' . print_r( $existing_product, true ) . ' </pre><br> ' . " \n";

	if ( !empty( $existing_product ) ) {
		return true;
	}

	//Woocommerce CRUD
	$obj_product = new WC_Product_Simple();

	$obj_product->set_name('payed_comment_technical_product'); //Set product name.
	$obj_product->set_status('publish'); //Set product status.
	$obj_product->set_virtual(true);
	$obj_product->set_catalog_visibility('hidden'); //Set catalog visibility.	| string $visibility Options: 'hidden', 'visible', 'search' and 'catalog'.
	$obj_product->set_description( __( 'This is technical product (for coment) which is not displayed on front-end. It is only required so that Payed Posts can work.', 'payed-posts' ) ); //Set product description.
	$obj_product->set_sold_individually(true); //Set if should be sold individually.            | bool
	$obj_product->set_reviews_allowed(false); //Set if reviews is allowed.                        | bool

	$new_product_id = $obj_product->save(); //Saving the data to create new product, it will return product ID.
}