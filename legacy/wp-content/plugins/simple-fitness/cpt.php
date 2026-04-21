<?php

// register custom post types
add_action( 'init', 'ozzsf_create_posttype', 0 );
function ozzsf_create_posttype() {
	// PROGRAMS
	// Set UI labels for Тренировка
	$labels = array(
		'name'                => _x( 'Тренировки', 'Тренировки', 'twentytwentytwo' ),
		'singular_name'       => _x( 'Тренировка', 'Тренировка', 'twentytwentytwo' ),
		'menu_name'           => __( 'Тренировки', 'twentytwentytwo' ),
		'all_items'           => __( 'Тренировки', 'twentytwentytwo' ),
		'view_item'           => __( 'Просмотр тренировки', 'twentytwentytwo' ),
		'add_new_item'        => __( 'Добавить тренировку', 'twentytwentytwo' ),
		'add_new'             => __( 'Добавить новую', 'twentytwentytwo' ),
		'edit_item'           => __( 'Редактировать тренировку', 'twentytwentytwo' ),
		'update_item'         => __( 'Сохранить тренировку', 'twentytwentytwo' ),
		'search_items'        => __( 'Искать тренировку', 'twentytwentytwo' ),
		'not_found'           => __( 'Не найдено', 'twentytwentytwo' ),
		'not_found_in_trash'  => __( 'Не найдено в удалённых', 'twentytwentytwo' ),
	);
	// Set other options for Тренировка
	$args = array(
		'label'               => __( 'тренировки', 'twentytwentytwo' ),
		'description'         => __( 'Тренировки', 'twentytwentytwo' ),
		'labels'              => $labels,
		// Features this CPT supports in Post Editor
		'supports'            => array( 'title', 'excerpt', 'author', 'thumbnail', 'comments', 'revisions' ),
		// You can associate this CPT with a taxonomy or custom taxonomy. 
		'taxonomies'          => array( 'post_tag' ),
		/* A hierarchical CPT is like Pages and can have
		* Parent and child items. A non-hierarchical CPT
		* is like Posts.
		*/ 
		'hierarchical'        => false,
		'public'              => true,
		'show_ui'             => true,
		'show_in_menu'        => 'ozzsf',
		'show_in_nav_menus'   => true,
		'show_in_admin_bar'   => true,
		'menu_position'       => 5,
		'can_export'          => true,
		'has_archive'         => true,
		'exclude_from_search' => false,
		'publicly_queryable'  => true,
		'capability_type'     => 'post',
		'show_in_rest'        => true,
 
	);
	// Registering Тренировка post type
	register_post_type( 'program', $args );

	// EXERCISES
	// Set UI labels for Упражнение
	$labels = array(
		'name'                => _x( 'Упражнения', 'Упражнения', 'twentytwentytwo' ),
		'singular_name'       => _x( 'Упражнение', 'Упражнение', 'twentytwentytwo' ),
		'menu_name'           => __( 'Упражнения', 'twentytwentytwo' ),
		'all_items'           => __( 'Упражнения', 'twentytwentytwo' ),
		'view_item'           => __( 'Просмотр упражнения', 'twentytwentytwo' ),
		'add_new_item'        => __( 'Добавить упражнение', 'twentytwentytwo' ),
		'add_new'             => __( 'Добавить новое', 'twentytwentytwo' ),
		'edit_item'           => __( 'Редактировать упражнение', 'twentytwentytwo' ),
		'update_item'         => __( 'Сохранить упражнение', 'twentytwentytwo' ),
		'search_items'        => __( 'Искать упражнение', 'twentytwentytwo' ),
		'not_found'           => __( 'Не найдено', 'twentytwentytwo' ),
		'not_found_in_trash'  => __( 'Не найдено в удалённых', 'twentytwentytwo' ),
	);
	// Set other options for Упражнение
	$args = array(
		'label'               => __( 'упражнения', 'twentytwentytwo' ),
		'description'         => __( 'Упражнения', 'twentytwentytwo' ),
		'labels'              => $labels,
		// Features this CPT supports in Post Editor
		'supports'            => array( 'title', 'excerpt', 'author', 'thumbnail', 'comments', 'revisions', 'custom-fields' ),
		// You can associate this CPT with a taxonomy or custom taxonomy. 
		'taxonomies'          => array( 'post_tag', 'exercise_type' ),
		/* A hierarchical CPT is like Pages and can have
		* Parent and child items. A non-hierarchical CPT
		* is like Posts.
		*/ 
		'hierarchical'        => false,
		'public'              => true,
		'show_ui'             => true,
		'show_in_menu'        => 'ozzsf',
		'show_in_nav_menus'   => true,
		'show_in_admin_bar'   => true,
		'menu_position'       => 5,
		'can_export'          => true,
		'has_archive'         => true,
		'exclude_from_search' => false,
		'publicly_queryable'  => true,
		'capability_type'     => 'post',
		'show_in_rest'        => true,
 
	);
	// Registering Упражнение post type
	register_post_type( 'exercise', $args );
}