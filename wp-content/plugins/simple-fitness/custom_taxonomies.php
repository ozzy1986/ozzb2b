<?php


// register custom taxonomy
add_action( 'init', 'ozzsf_register_exercise_type_taxonomy', 10 );
function ozzsf_register_exercise_type_taxonomy() {

	$labels = array(
		'name'				=> _x( 'Типы нагрузки', 'taxonomy general name', 'twentytwentytwo' ),
		'singular_name'		=> _x( 'Тип нагрузки', 'taxonomy singular name', 'twentytwentytwo' ),
		'search_items'		=> __( 'Поиск по типу нагрузки', 'twentytwentytwo' ),
		'all_items'			=> __( 'Все типы нагрузки', 'twentytwentytwo' ),
		'parent_item'		=> __( 'Родительский тип нагрузки', 'twentytwentytwo' ),
		'parent_item_colon'	=> __( 'Родительский тип нагрузки:', 'twentytwentytwo' ),
		'edit_item'			=> __( 'Редактировать тип нагрузки', 'twentytwentytwo' ), 
		'update_item'		=> __( 'Сохранить тип нагрузки', 'twentytwentytwo' ),
		'add_new_item'		=> __( 'Добавить новый тип нагрузки', 'twentytwentytwo' ),
		'new_item_name'		=> __( 'Название типа нагрузки', 'twentytwentytwo' ),
		'menu_name'			=> __( 'Типы тренировок', 'twentytwentytwo' ),
	);    

	// Now register the taxonomy
	register_taxonomy( 'exercise_type', array( 'exercise', 'program' ), array(
		'hierarchical'		=> true,
		'labels'			=> $labels,
		'show_ui'			=> true,
		'show_in_menu'		=> true,
		'show_in_rest'		=> true,
		'show_admin_column'	=> true,
		'query_var'			=> true,
		//'rewrite'			=> array( 'slug' => 'exercise_type' ),
	));
}
// show it in admin menu
add_action( 'admin_menu', 'ozzsf_show_exercise_type_in_admin_menu' );
function ozzsf_show_exercise_type_in_admin_menu() {
	add_submenu_page(
		'ozzsf',
		__( 'Типы нагрузки', 'twentytwentytwo' ),
		__( 'Типы нагрузки', 'twentytwentytwo' ),
		'manage_options',
		'edit-tags.php?taxonomy=exercise_type',
	);
}
add_action( 'parent_file', 'ozzsf_highlight_exercise_type_menu' );
function ozzsf_highlight_exercise_type_menu( $parent_file ) {
	global $current_screen;

    $taxonomy = $current_screen->taxonomy;
    if ( $taxonomy == 'exercise_type' ) {
        $parent_file = 'ozzsf';
    }

    return $parent_file;
}
