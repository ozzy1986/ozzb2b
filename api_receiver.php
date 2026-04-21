<?php
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);

session_start();

require_once 'db.php';
require_once 'functions.php';

set_time_limit(0);

// echo '<br>GET:<pre>'.print_r($_GET, true).'</pre>';
// echo '<br>POST:<pre>'.print_r($_POST, true).'</pre>';

$result = 'error';
$data	= [
	'error'		=> '1',
	'message'	=> 'No parameters for call',
	'status'	=> '400'
];

// USER AUTHENTICATION CALL
if (isset($_GET['action']) and $_GET['action'] == 'auth_user') {
	$input = file_get_contents('php://input');
	if ($input) {
		$input_data	= json_decode($input, true);
		if (!empty($input_data['data'])) {
			$_POST = $input_data['data'];	
		} else {
			$result = 'error';
			$data	= [
				'error'		=> '0',
				'message'	=> 'No data was passed',
				'status'	=> '400'
			];
			echo json_encode([
				'result'	=> $result,
				'data'		=> $data
			]);
			exit;
		}
	} else {
		$result = 'error';
		$data	= [
			'error'		=> '0',
			'message'	=> 'No data was passed',
			'status'	=> '400'
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	}

	// check if login and password are set
	if (empty($_POST['login']) or empty($_POST['password'])) {
		$result = 'error';
		$data	= [
			'error'		=> '2',
			'message'	=> 'Login and/or password not set',
			'status'	=> '400'
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	}

	// check if username is not occupied
	$username	= $mysqli->real_escape_string($_POST['login']);
	$check		= $mysqli->query("SELECT * FROM users WHERE `username` LIKE '".$username."'");
	if (empty($check) or empty($check->num_rows)) {
		// no such user
		$result = 'error';
		$data	= [
			'error'		=> '3',
			'message'	=> 'No such user',
			'status'	=> '400'
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	} else {
		// get the user from db
		$result = $mysqli->query("SELECT * FROM users WHERE `username` LIKE '".$username."'");
		if (!empty($result->num_rows)) {
			$user = $result->fetch_assoc();

			// verify password
			if (password_verify($_POST['password'], $user['password'])) {
				// check if password needs rehashing
			    if (password_needs_rehash($user['password'], PASSWORD_DEFAULT)) {
			        $new_hash = password_hash($_POST['password'], PASSWORD_DEFAULT);
			        $rehash = $mysqli->query("UPDATE `users` SET `password` = '".$new_hash."' WHERE `username` = '".$_POST['username']."'");
			    }

			    // user authenticated successfully, store him
			    // $_SESSION['user_id'] = $user['id'];
				unset($user['password']);

			    // generate jwt token
			    $jwt = create_jwt(['user' => $user]);


	    		$result = 'success';
				$data	= [
					'success'	=> '1',
					'message'	=> ['jwt' => $jwt, 'user' => $user]
				];
				echo json_encode([
					'result'	=> $result,
					'data'		=> $data
				]);
				exit;
			} else {
				$result = 'error';
				$data	= [
					'error'		=> '4',
					'message'	=> 'Password incorrect',
					'status'	=> '400'
				];
				echo json_encode([
					'result'	=> $result,
					'data'		=> $data
				]);
				exit;
			}
		} else {
			$result = 'error';
			$data	= [
				'error'		=> '3',
				'message'	=> 'No such user',
				'status'	=> '400'
			];
			echo json_encode([
				'result'	=> $result,
				'data'		=> $data
			]);
			exit;
		}
	}
}


// CALL FOR GETTING ALL USERS
if (isset($_GET['action']) and $_GET['action'] == 'get_all_users') {

	// check jwt token first
	// $token = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
	// if (!is_valid_jwt($token)) {
	// 	$result = 'error';
	// 	$data	= [
	// 		'error'		=> '99',
	// 		'message'	=> 'Token is incorrect or not set',
			// 'status'	=> '400'
	// 	];
	// 	echo json_encode([
	// 		'result'	=> $result,
	// 		'data'		=> $data
	// 	]);
	// 	exit;
	// }

	$query = "SELECT * FROM users WHERE `confirmed` = '1' ";
	$all_users = $mysqli->query($query);
	if (empty($all_users) or empty($all_users->num_rows)) {
		$result = 'error';
		$data	= [
			'error'		=> '19',
			'message'	=> 'No users found',
			'status'	=> '400'
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	} else {
		// get and return users
		$users = [];
		while ($user = $all_users->fetch_assoc()) {
			unset($user['password']);	
			unset($user['confirmed']);
			$users[$user['id']]	= $user;
		}
		

		$result = 'success';
		$data	= [
			'success'			=> '1',
			'message'			=> 'User found',
			'all_users_data'	=> $users,
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	}
}

// CALL FOR GETTING OUR SINGLE PRODUCT
if (isset($_GET['action']) and $_GET['action'] == 'get_our_single_product') {

	// check jwt token first
	// $token = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
	// if (!is_valid_jwt($token)) {
	// 	$result = 'error';
	// 	$data	= [
	// 		'error'		=> '99',
	// 		'message'	=> 'Token is incorrect or not set',
				// 'status'	=> '400'
	// 	];
	// 	echo json_encode([
	// 		'result'	=> $result,
	// 		'data'		=> $data
	// 	]);
	// 	exit;
	// }

	$input = file_get_contents('php://input');
	if ($input) {
		$input_data	= json_decode($input, true);
		// echo '<br>input_data:<pre>'.print_r($input_data, true).'</pre>';
		if (!empty($input_data['data'])) {
			$_POST = $input_data['data'];	
		} else {
			$result = 'error';
			$data	= [
				'error'		=> '0',
				'message'	=> 'No data was passed 1',
				'status'	=> '400'
			];
			echo json_encode([
				'result'	=> $result,
				'data'		=> $data
			]);
			exit;
		}
	} else {
		$result = 'error';
		$data	= [
			'error'		=> '0',
			'message'	=> 'No data was passed 2',
			'status'	=> '400'
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	}

	$sku = intval($_POST['sku']);

	$query = "SELECT * FROM own_products WHERE `sku` = '".$sku."' LIMIT 1";
	$product_result = $mysqli->query($query);
	if (empty($product_result) or empty($product_result->num_rows)) {
		$result = 'error';
		$data	= [
			'error'		=> '19',
			'message'	=> 'Product not found',
			'status'	=> '400'
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	} else {
		// get and return product
		$product = $product_result->fetch_assoc();
		
		$result = 'success';
		$data	= [
			'success'			=> '1',
			'message'			=> 'Product found',
			'product_data'		=> $product,
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	}
}

// CALL FOR GETTING OUR PRODUCTS
if (isset($_GET['action']) and $_GET['action'] == 'get_our_products') {

	// check jwt token first
	// $token = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
	// if (!is_valid_jwt($token)) {
	// 	$result = 'error';
	// 	$data	= [
	// 		'error'		=> '99',
	// 		'message'	=> 'Token is incorrect or not set',
				// 'status'	=> '400'
	// 	];
	// 	echo json_encode([
	// 		'result'	=> $result,
	// 		'data'		=> $data
	// 	]);
	// 	exit;
	// }

	$query = "SELECT * FROM own_products WHERE 1=1 ";
	$all_products = $mysqli->query($query);
	if (empty($all_products) or empty($all_products->num_rows)) {
		$result = 'error';
		$data	= [
			'error'		=> '19',
			'message'	=> 'No products found',
			'status'	=> '400'
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	} else {
		// get and return products
		$products = [];
		while ($product = $all_products->fetch_assoc()) {
			$products[$product['id']] = $product;
		}

		$result = 'success';
		$data	= [
			'success'			=> '1',
			'message'			=> 'Products found',
			'all_products_data'	=> $products,
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	}
}

// CALL FOR GETTING LEADERS BY PRODUCT
if (isset($_GET['action']) and $_GET['action'] == 'get_leaders') {

	// check jwt token first
	// $token = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
	// if (!is_valid_jwt($token)) {
	// 	$result = 'error';
	// 	$data	= [
	// 		'error'		=> '99',
	// 		'message'	=> 'Token is incorrect or not set',
				// 'status'	=> '400'
	// 	];
	// 	echo json_encode([
	// 		'result'	=> $result,
	// 		'data'		=> $data
	// 	]);
	// 	exit;
	// }

	$sku = intval($_POST['sku']);

	$leaders = find_leaders_30($sku);

	if (empty($leaders)) {
		$result = 'error';
		$data	= [
			'error'		=> '19',
			'message'	=> 'No leaders found',
			'status'	=> '400'
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	} else {
		// return leaders
		$result = 'success';
		$data	= [
			'success'			=> '1',
			'message'			=> 'Leaders found',
			'leaders_data'		=> $leaders,
		];
		echo json_encode([
			'result'	=> $result,
			'data'		=> $data
		]);
		exit;
	}
}

echo json_encode([
	'result'	=> $result,
	'data'		=> $data
]);
exit;
?>