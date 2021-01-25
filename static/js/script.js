function resize(){
	var windowWidth = $(window).width();
	var windowHeight = $(window).height();
	
	function changeContentWidth(){
		var sidebarWidth = $('#sidebar').outerWidth();
		var rightMenuWidth = $('#rightMenu').outerWidth();
		var contentWidth = windowWidth - (sidebarWidth + rightMenuWidth);
		var contentWidthFull = windowWidth - sidebarWidth;
		$('#main').width(contentWidth);
		$('#main.full').width(contentWidthFull);
	}
	
	function changeMenuHeight(){
		var headerHeight = $('#header').outerHeight();
		var sidebarHeight = windowHeight - headerHeight;
		
		$('#menuContainer').height(sidebarHeight);
		$('#menuContainer').perfectScrollbar('update');
		
		$('#rightMenuContainer').height(sidebarHeight);
		$('#rightMenuContainer').perfectScrollbar('update');
	}
	
	var popupHeight = $('.popupBox .popupInner').outerHeight();
	$('.popupBox').height(popupHeight);
	
	changeContentWidth();
	changeMenuHeight();
	
	function equal_grid_content(){
		var height = 0;
		$('ul.grid.details li .content').each(function(){
			var h = $(this).height();
			if (h > height){
				height = h;
			}
		});
		$('ul.grid.details li .content').height(height);
	}
	equal_grid_content();
	
	function changePopupBox(){
		var avHeight = windowHeight - 90;
		$('.item_popup').height(avHeight);
		var headHeight = $('.item_popup .head').outerHeight();
		var itemHeight = avHeight - headHeight - 25;
		$('.item_popup section.short').height(itemHeight);
		$('.item_popup section.scroll').height(itemHeight);
		$('#menuContainer').perfectScrollbar('update');
		
		//$('#rightMenuContainer').height(itemHeight);
		//$('#rightMenuContainer').perfectScrollbar('update');
	}
	changePopupBox();
}

function scroll_to_error_message(selector,vert_no){
    // selector should return one element
    // vert_no is the height from top to element visibile
    if(selector===undefined) selector = '.errorlist:first';
    if(vert_no===undefined) vert_no = 200;
    if($('.errorlist:first').length){
        $('html, body').animate({ scrollTop: $(selector).offset().top - vert_no } , 500);
    }

}

function show_loader(){
	$('.popupBg').show();
	$('.popupBox').remove();
	$('body').append('<section class="popupBox"><section class="popupInner"><span class="loader"></span></section></section>');
	resize();
}

function remove_popup_box(){
	$('.popupBox').remove();	
	$('.popupBg').hide();	
}

$(document).ready(function(){
	resize();
	
	$('#tabs').tabs();
	$('html').click(function() {
		var visible = $('#profileInfoDetails').is(':visible');
		if (visible){
			$('#profileInfoDetails').toggle();
		}
	});
	
	$('#header section.right div.profile span.thumb').click(function(event){
		event.stopPropagation();
		var offset = $(this).offset();
		
		var visible = $('#profileInfoDetails').is(':visible');
		if (visible){
			$('#profileInfoDetails').toggle();
		}else{
			var profile = $(this).parents('.profile').find('.info').html();
			$('#profileInfoDetails').remove();
			$('body').append('<div id="profileInfoDetails"> ' + profile + '</div>');
			$('#profileInfoDetails').css({
				'top' : offset.top + 50
			});
		}		
		
	});
	
	$('#content.list table tr td span.action').click(function(event){
		event.stopPropagation();
		var offset = $(this).offset();
		var offset_parent = $(this).parents('.widget').offset();
		var offset_left = offset.left - offset_parent.left;
		var offset_top = offset.top - offset_parent.top;
		var $actions = $(this).parents('td').find('div.actions');
		var $parent_tr = $(this).parents('tr');
		$('#content.list table tr td div.actions').not($actions).hide();
		$actions.toggle().css({
			'top' : offset_top + 130,
			'left' : offset_left - 58
		});
		$('#content.list table tr').not($parent_tr).removeClass('active');
		$(this).parents('tr').toggleClass('active');
	});
	
	$('#content.list table tr td div.actions').hover(function(){
		
	},function(){
		$(this).hide();
		$(this).parents('tr').toggleClass('active');
	});
	
	$('#menuContainer').perfectScrollbar({
		suppressScrollX : true,
		wheelSpeed : 60,
		wheelPropagation : true
	});
	
	$('#rightMenuContainer').perfectScrollbar({
		suppressScrollX : true,
		wheelSpeed : 60,
		wheelPropagation : true
	});
	
	$('.item_popup section.scroll').perfectScrollbar({
		suppressScrollX : true,
		wheelSpeed : 60,
		wheelPropagation : true
	});
	
	$("select.single").selectOrDie({
	    cycle: true,
	    size: 5
	});
	
	$('div.formElements label span.help').click(function(event){
		var $this = $(this);
		var offset_help = $(this).offset();
		var offset_parent = $(this).parents('div.field').offset();
		var offset_left = offset_help.left - offset_parent.left;
		var offset_top = offset_help.top - offset_parent.top;
		var left = offset_left - 10;
		var top = offset_top + 35; 
		var help_text = $(this).parents('div.field').find('span.help_text');
		$('div.field span.help_text').not(help_text).hide();
		$(this).parents('div.field').find('span.help_text').css({
			"left" : left,
			"top" : top
		}).toggle();
		
		$(document).mouseup(function (e){
		    var container = help_text;	
		    var container2 = $this;	
		    if (!container.is(e.target) && container.has(e.target).length === 0 && !container2.is(e.target) && container2.has(e.target).length === 0){
		        container.hide();
		    }
		});
	});
	
	$('#head div.actions .icons .filter').click(function(e){
		e.preventDefault();
		$(this).parents('div.actions').find('.filter_form').toggle();
	});
	
	
	$('form').checkBo();
	$('input:checkbox').each(function(){
		if ($(this).prop('checked')){
			$(this).prop('checked', true).change();
		}else{
			$(this).prop('checked', false).change();
		}
	});
	$('.cb-radio').removeClass('checked');
	$('input:radio').each(function(){
		if ($(this).prop('checked')){
			$(this).parents('.cb-radio').addClass('checked');
		}else{
			$(this).parents('.cb-radio').removeClass('checked');
		}
	});
	$(document).on('click','.check_all_box',function(){
		$parentLi = $(this).parent('li');
		var unchecked = $parentLi.find('ul li input:checkbox:not(":checked")').length;
		if (unchecked > 0){
			$parentLi.find('input:checkbox').prop('checked', true).change();
		}else{
			$parentLi.find('input:checkbox').prop('checked', false).change();
		}		
	});
	
	$('body').on("focus","input.datepicker", function(){
	    $(this).datepicker({
	    	dateFormat : 'dd/mm/yy',
	    	inline: true,  
            showOtherMonths: true, 
            changeMonth : true,
			changeYear : true,  
            dayNamesMin: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], 
	    });
	});
	$('body').on("focus","input.datetimepicker", function(){
	    $(this).datetimepicker({
	    	changeMonth : true,
			changeYear : true,
			dateFormat : 'dd/mm/yy',
			yearRange : '2014:2050'
		});
	});
	
	$('.add_item_container .icon_add_item').click(function(){
		var $nearTable = $(this).parents('.add_item_container').find('table');
		var $second_last_tr = $nearTable.find('tr:nth-last-child(2)');
		var rowTemp = $nearTable.find('tr:nth-last-child(2)').html();
		$second_last_tr.after('<tr class="form_set_row">' + rowTemp + '</tr>');
		$second_last_tr.find('tr:last-child input').removeAttr('id');
		$second_last_tr.find('tr:last-child input').removeClass('hasDatepicker');
	});
	
	$(document).on('click','.form_set_row .icon-trash', function(){
		var $this = $(this);
		$parent_table = $this.parents('table');
		var length = $parent_table.find('tr').length;
		if(length > 3){
			$this.parents('tr').remove();
		}
	});
	
	$(document).on('click','.popupBox span.close,.popupBox span.cancel',function(){
		$(this).parents('.popupBox').remove();
		$('.popupBg').hide();		
	});
	
	$('a.showPopup').click(function(){
		var $this = $(this);
		var popup = $this.attr('data-popup');
		$('.popupBg').show();
		$('.item_popup.' + popup).show();
		resize();
	});
	
	$(document).on('click','.item_popup section.head .close',function(){
		$(this).parents('.item_popup').hide();
		$('.popupBg').hide();		
	});
	
	function append_to_select(selector,value,text){
		$(selector).append('<option value="'+ value + '">'+ text + '</option>');
		$(selector).multiSelect('refresh');
	}
	
	$(document).on('click','.add_pop_action',function(e){
		e.preventDefault();
		var $this = $(this);
		var url = $this.attr('href');
		var title = $this.attr('data-title');
		var input_class = $this.attr('data-class');
		var isReload = $this.hasClass('reload');
		var runFunction = $this.hasClass('runFunction');
		var functionName = $this.attr('data-function');
		var selectorName = $this.attr('data-selector');
		var formClass = "ajax";
		if (runFunction){
			formClass += " runFunction";
		}	
		
		$('.popupBg').show();
		$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><form data-selector="' + selectorName + '" data-function="' + functionName + '" class="' + formClass + '" action="' + url + '"><div class="content"><input name="data" class="' + input_class + '" type="text" placeholder="' + title + '"/></div><div class="buttons"><input type="submit" class="button color_1" value="Submit"/></div></form><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
		resize();
	});
	
	function getCookie(name) {
	    var cookieValue = null;
	    if (document.cookie && document.cookie != '') {
	        var cookies = document.cookie.split(';');
	        for (var i = 0; i < cookies.length; i++) {
	            var cookie = jQuery.trim(cookies[i]);
	            // Does this cookie string begin with the name we want?
	            if (cookie.substring(0, name.length + 1) == (name + '=')) {
	                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
	                break;
	            }
	        }
	    }
	    return cookieValue;
	}
	$(document).on('click','.cancelit',function(e){
		e.preventDefault();
		var $this = $(this);
		var url = $this.attr('data-url');
		var title = $this.attr('data-title');
		if(!title){
			title = "Are you sure?";
		}
		var alert_message = $this.attr('data-message');
		var showAlert = $this.hasClass('with_alert');
		function cancelit(){
			show_loader();
			$.ajax({
				type : 'GET',
				url : url,
				dataType : 'json',
				success : function(data){
					var title = data['title'];	
					var status = data['status'];
					var message = data['message'];
					$('.popupBox').remove();

					if (status == 'true') {
						if (!title){				
							title = "Success";
						}
						$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content"><p><strong>' + message + '</strong></p></div></section></section>');						
						resize();
						window.setTimeout(function() {						
							remove_popup_box();	
						}, 3000);
						window.setTimeout(function() {						
							show_loader();
							window.location.reload();	
						}, 3000);
					}
					else{
						if (!title){				
							title = "An Error Occurred";
						}

						$('.popupBox').remove();
						$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content"><p>' + message + '</p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
						resize();
						window.setTimeout(function() {						
							remove_popup_box();	
						}, 3000);
					}
				},
				error : function(data) {
					
					$('.popupBox').remove();
					$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>An error occurred</h3></div><div class="content"><p>An error occurred. Please try again later. </p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
					resize();
					window.setTimeout(function(){						
						remove_popup_box();
					}, 3000);
				}
			});
		}
		if (showAlert){
			$('.popupBg').show();
			$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content"><p>' + alert_message + '</p></div><div class="buttons"><span class="link proceed">Proceed</span><span class="link cancel">Cancel</span></div></section></section>');
			resize();
			
			$('.popupBox .proceed').click(function(){
				remove_popup_box();	
				cancelit()
			});
		}

	});

	$(document).on('click','.doit',function(e){
		e.preventDefault();
		var $this = $(this);
		var id = $this.attr('data-id');
		var url = $this.attr('data-url');
		var title = $this.attr('data-title');
		if(!title){
			title = "Are you sure?";
		}
		var alert_message = $this.attr('data-message');
		var isReload = $this.hasClass('reload');
		var isRedirect = $this.hasClass('redirect');
		var showAlert = $this.hasClass('with_alert');
		var showPassword = $this.hasClass('with_password');
		var runFunction = $this.hasClass('run_function');
		var function_name = $this.attr('data-function');
			
		function doit(){
			show_loader();
			
			jQuery.ajax({
				type : 'GET',
				url : url,
				dataType : 'json',
				data : {
					uuid : id
				},
				success : function(data) {
					var message = data['message'];
					var status = data['status'];
					var redirect = data['redirect'];
					var redirect_url = data['redirect_url'];
					var stable = data['stable'];
					var title = data['title'];	
					
					$('.popupBox').remove();
					if (status == 'true') {
						if (title){
							title = title;
						}else{
							title = "Success";
						}
						
						$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content"><p>' + message + '</p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
						resize();
						
						if (stable != "true"){					
							window.setTimeout(function() {						
								remove_popup_box();				
								if (isRedirect && redirect == 'true') {
									window.location.href = redirect_url;
								}
								if (isReload) {
									window.location.reload();
								}					
							}, 3000);	
						}	
					}else{
						if (title){
							title = title;
						}else{
							title = "An Error Occurred";
						}			
						$('.popupBox').remove();
						$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content"><p>' + message + '</p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
						resize();
						
						if (stable != "true"){					
							window.setTimeout(function() {						
								remove_popup_box();	
							}, 3000);	
						}	
					}
				},
				error : function(data) {
					console.log(data);
					$('.popupBox').remove();
					$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>An error occurred</h3></div><div class="content"><p>An error occurred. Please try again later. </p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
					resize();
					window.setTimeout(function() {						
						remove_popup_box();
					}, 3000);
				}
			});
		}
		if (showAlert){
			$('.popupBg').show();
			$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content"><p>' + alert_message + '</p></div><div class="buttons"><span class="link proceed">Proceed</span><span class="link cancel">Cancel</span></div></section></section>');
			resize();
			
			$('.popupBox .proceed').click(function(){
				remove_popup_box();
				
				if (showPassword){
					var csrftoken = getCookie('csrftoken');		
								
					$('.popupBg').show();
					$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>Enter your password</h3></div><div class="content"><input name="password" class="password" type="password" placeholder="Enter your password"/></div><div class="buttons"><input type="submit" class="button color_1 proceed" value="Submit"/></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
					resize();
					
					$('.popupBox .proceed').click(function(){
						
						show_loader();
						
						var password = $(this).parents('.popupBox').find('input.password').val();						
						var url = $this.attr('data-url');
						
						jQuery.ajax({
							type : 'POST',
							url : url,
							dataType : 'json',
							data : {
								password : password,
								csrfmiddlewaretoken : csrftoken
							},
							success : function(data) {
								var message = data['message'];
								var status = data['status'];
								var redirect = data['redirect'];
								var redirect_url = data['redirect_url'];
								var stable= data['stable'];
								var title = data['title'];	
								
								$('.popupBox').remove();
								if (status == 'true') {
									if (title){
										title = title;
									}else{
										title = "Success";
									}
									
									$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content"><p>' + message + '</p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
									resize();
									
									if (stable != "true"){					
										window.setTimeout(function() {						
											remove_popup_box();				
											if (isRedirect && redirect == 'true') {
												window.location.href = redirect_url;
											}
											if (isReload) {
												window.location.reload();
											}					
										}, 3000);	
									}	
								}else{
									if (title){
										title = title;
									}else{
										title = "An Error Occurred";
									}			
									$('.popupBox').remove();
									$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content"><p>' + message + '</p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
									resize();
									
									if (stable != "true"){					
										window.setTimeout(function() {						
											remove_popup_box();	
										}, 3000);	
									}	
								}
							},
							error : function(data) {
								console.log(data);
								$('.popupBox').remove();
								$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>An error occurred</h3></div><div class="content"><p>An error occurred. Please try again later. </p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
								resize();
								window.setTimeout(function() {						
									remove_popup_box();
								}, 3000);
							}
						});		
					});	
				}else{
					doit();
				}			
			});	
		}else{
			doit();
		}
	});
	
	$(document).on('change','select.change_select_function',function(){
		var $this = $(this);
		var url = $this.attr('data-url');
		var isReload = $this.hasClass('reload');
		var data = $this.val();
		
		show_loader();
		
		jQuery.ajax({
			type : "GET",
			url : url,
			dataType : 'json',
			data : {
				data : data
			},
			success : function(data) {
				var message = data['message'];
				var status = data['status'];
				var stable = data['stable'];
				var redirect = data['redirect'];
				var redirect_url = data['redirect_url'];
				
				$('.popupBox').remove();
				$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>Success</h3></div><div class="content"><p>' + message + '</p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
				resize();
				
				if (stable != "true"){					
					window.setTimeout(function() {						
						$('.popupBox').remove();	
						$('.popupBg').hide();						
						if (redirect == 'true') {
							window.location.href = redirect_url;
						}
						if (isReload) {
							window.location.reload();
						}					
					}, 3000);	
				}
			},
			error : function(data){
				$('.popupBox').remove();
				$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>An error occurred</h3></div><div class="content"><p>An error occurred. Please try again later. </p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
				resize();
				window.setTimeout(function() {						
					remove_popup_box();
				}, 3000);	
			}
			
		});
	});
	
	$(document).on('submit', 'form.ajax', function(e){	
		e.preventDefault();
		var $this = $(this);
		$this.validate({
			rules : {
				required_field : "required",
				password1: "required",
			    password2: {
			    	equalTo: "#id_password1"
			    }
			}
		});
		var valid = $this.valid();
		if (valid){
			var url = $this.attr('action');
			var method = $this.attr('method');
			var isReset = $this.hasClass('resetForm');
			var isReload = $this.hasClass('reload');
			var data = $this.serialize();
			var runFunction = $this.hasClass('runFunction');
			var functionName = $this.attr('data-function');
			var selectorName = $this.attr('data-selector');
			
			show_loader();
			
			jQuery.ajax({
				type : method,
				url : url,
				dataType : 'json',
				data : data,
				success : function(data) {
					
					var message = data['message'];
					var status = data['status'];
					var title = data['title'];	
					var redirect = data['redirect'];
					var redirect_url = data['redirect_url'];
					var stable = data['stable'];
					var output_value = data['output_value'];
					var output_text = data['output_text'];
					var pk = data['pk'];
					
					if (status == 'true') {
						if (title){
							title = title;
						}else{
							title = "Success";
						}
						$('.popupBox').remove();
						$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content"><p>' + message + '</p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
						resize();
						
						if(runFunction){						
							if (functionName == "append_to_select"){
								append_to_select(selectorName,output_value,output_text);
							}
							
							if (functionName == "add_to_customized_item"){
								var color = $('#id_color').val();
								var size = $('#id_size').val();
								var name = $('#id_name').val();
								var c_name = name + "(" + color + "," + size + ")";
								var unit = $('#id_unit').val();
								var price = $('#id_price').val();
								var qty = $('#id_store_item_qty').val();
								add_to_customized_item(pk,c_name,unit,price,qty);
							}
						}
						
						if (isReset) {
							$this[0].reset();
							$this.find("select").selectOrDie("update");
						}
						
						if (stable != "true"){					
							window.setTimeout(function() {						
								remove_popup_box();		
								if ($('.item_popup').is(':visible')){
									$('.popupBg').show();
								}		
								if (redirect == 'true') {
									window.location.href = redirect_url;
								}
								if (isReload) {
									window.location.reload();
								}					
							}, 3000);	
						}						
					}else{			
						if (title){
							title = title;
						}else{
							title = "An Error Occurred";
						}			
						$('.popupBox').remove();
						
						/*$display_loader = String();
						$display_loader += '<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content">'
						$obj_keys = Object.keys(message);
						for ($obj_key in $obj_keys){
							$display_loader += '<p>' + message[$obj_keys[$obj_key]] + '</p>'
						}
						$display_loader += '</div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>'
						$('body').append($display_loader);
						*/
						$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>' + title + '</h3></div><div class="content"><p>' + message + '</p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
						resize();
						
						if (stable != "true"){					
							window.setTimeout(function() {						
								remove_popup_box();	
								if ($('.item_popup').is(':visible')){
									$('.popupBg').show();
								}
							}, 3000);	
						}	
					}					
					
				},
				error : function(data) {
					console.log(data);
					$('.popupBox').remove();
					$('body').append('<section class="popupBox"><section class="popupInner"><div class="head"><h3>An error occurred</h3></div><div class="content"><p>An error occurred. Please try again later. </p></div><div class="buttons"><span class="link cancel">Cancel</span></div></section></section>');
					resize();
					window.setTimeout(function() {						
						remove_popup_box();
					}, 3000);
				}
			});		
		}
	});	
});

$(window).resize(function(){
	resize();
});

$(window).load(function(){
	resize();
});

/* form validation*/
(function(e){e.extend(e.fn,{validate:function(t){if(!this.length){if(t&&t.debug&&window.console){console.warn("Nothing selected, can't validate, returning nothing.")}return}var n=e.data(this[0],"validator");if(n){return n}this.attr("novalidate","novalidate");n=new e.validator(t,this[0]);e.data(this[0],"validator",n);if(n.settings.onsubmit){this.validateDelegate(":submit","click",function(t){if(n.settings.submitHandler){n.submitButton=t.target}if(e(t.target).hasClass("cancel")){n.cancelSubmit=true}if(e(t.target).attr("formnovalidate")!==undefined){n.cancelSubmit=true}});this.submit(function(t){function r(){var r;if(n.settings.submitHandler){if(n.submitButton){r=e("<input type='hidden'/>").attr("name",n.submitButton.name).val(e(n.submitButton).val()).appendTo(n.currentForm)}n.settings.submitHandler.call(n,n.currentForm,t);if(n.submitButton){r.remove()}return false}return true}if(n.settings.debug){t.preventDefault()}if(n.cancelSubmit){n.cancelSubmit=false;return r()}if(n.form()){if(n.pendingRequest){n.formSubmitted=true;return false}return r()}else{n.focusInvalid();return false}})}return n},valid:function(){if(e(this[0]).is("form")){return this.validate().form()}else{var t=true;var n=e(this[0].form).validate();this.each(function(){t=t&&n.element(this)});return t}},removeAttrs:function(t){var n={},r=this;e.each(t.split(/\s/),function(e,t){n[t]=r.attr(t);r.removeAttr(t)});return n},rules:function(t,n){var r=this[0];if(t){var i=e.data(r.form,"validator").settings;var s=i.rules;var o=e.validator.staticRules(r);switch(t){case"add":e.extend(o,e.validator.normalizeRule(n));delete o.messages;s[r.name]=o;if(n.messages){i.messages[r.name]=e.extend(i.messages[r.name],n.messages)}break;case"remove":if(!n){delete s[r.name];return o}var u={};e.each(n.split(/\s/),function(e,t){u[t]=o[t];delete o[t]});return u}}var a=e.validator.normalizeRules(e.extend({},e.validator.classRules(r),e.validator.attributeRules(r),e.validator.dataRules(r),e.validator.staticRules(r)),r);if(a.required){var f=a.required;delete a.required;a=e.extend({required:f},a)}return a}});e.extend(e.expr[":"],{blank:function(t){return!e.trim(""+e(t).val())},filled:function(t){return!!e.trim(""+e(t).val())},unchecked:function(t){return!e(t).prop("checked")}});e.validator=function(t,n){this.settings=e.extend(true,{},e.validator.defaults,t);this.currentForm=n;this.init()};e.validator.format=function(t,n){if(arguments.length===1){return function(){var n=e.makeArray(arguments);n.unshift(t);return e.validator.format.apply(this,n)}}if(arguments.length>2&&n.constructor!==Array){n=e.makeArray(arguments).slice(1)}if(n.constructor!==Array){n=[n]}e.each(n,function(e,n){t=t.replace(new RegExp("\\{"+e+"\\}","g"),function(){return n})});return t};e.extend(e.validator,{defaults:{messages:{},groups:{},rules:{},errorClass:"error",validClass:"valid",errorElement:"label",focusInvalid:true,errorContainer:e([]),errorLabelContainer:e([]),onsubmit:true,ignore:":hidden",ignoreTitle:false,onfocusin:function(e,t){this.lastActive=e;if(this.settings.focusCleanup&&!this.blockFocusCleanup){if(this.settings.unhighlight){this.settings.unhighlight.call(this,e,this.settings.errorClass,this.settings.validClass)}this.addWrapper(this.errorsFor(e)).hide()}},onfocusout:function(e,t){if(!this.checkable(e)&&(e.name in this.submitted||!this.optional(e))){this.element(e)}},onkeyup:function(e,t){if(t.which===9&&this.elementValue(e)===""){return}else if(e.name in this.submitted||e===this.lastElement){this.element(e)}},onclick:function(e,t){if(e.name in this.submitted){this.element(e)}else if(e.parentNode.name in this.submitted){this.element(e.parentNode)}},highlight:function(t,n,r){if(t.type==="radio"){this.findByName(t.name).addClass(n).removeClass(r)}else{e(t).addClass(n).removeClass(r)}},unhighlight:function(t,n,r){if(t.type==="radio"){this.findByName(t.name).removeClass(n).addClass(r)}else{e(t).removeClass(n).addClass(r)}}},setDefaults:function(t){e.extend(e.validator.defaults,t)},messages:{required:"This field is required.",remote:"Please fix this field.",email:"Please enter a valid email address.",url:"Please enter a valid URL.",date:"Please enter a valid date.",dateISO:"Please enter a valid date (ISO).",number:"Please enter a valid number.",digits:"Please enter only digits.",creditcard:"Please enter a valid credit card number.",equalTo:"Please enter the same value again.",maxlength:e.validator.format("Please enter no more than {0} characters."),minlength:e.validator.format("Please enter at least {0} characters."),rangelength:e.validator.format("Please enter a value between {0} and {1} characters long."),range:e.validator.format("Please enter a value between {0} and {1}."),max:e.validator.format("Please enter a value less than or equal to {0}."),min:e.validator.format("Please enter a value greater than or equal to {0}.")},autoCreateRanges:false,prototype:{init:function(){function r(t){var n=e.data(this[0].form,"validator"),r="on"+t.type.replace(/^validate/,"");if(n.settings[r]){n.settings[r].call(n,this[0],t)}}this.labelContainer=e(this.settings.errorLabelContainer);this.errorContext=this.labelContainer.length&&this.labelContainer||e(this.currentForm);this.containers=e(this.settings.errorContainer).add(this.settings.errorLabelContainer);this.submitted={};this.valueCache={};this.pendingRequest=0;this.pending={};this.invalid={};this.reset();var t=this.groups={};e.each(this.settings.groups,function(n,r){if(typeof r==="string"){r=r.split(/\s/)}e.each(r,function(e,r){t[r]=n})});var n=this.settings.rules;e.each(n,function(t,r){n[t]=e.validator.normalizeRule(r)});e(this.currentForm).validateDelegate(":text, [type='password'], [type='file'], select, textarea, "+"[type='number'], [type='search'] ,[type='tel'], [type='url'], "+"[type='email'], [type='datetime'], [type='date'], [type='month'], "+"[type='week'], [type='time'], [type='datetime-local'], "+"[type='range'], [type='color'] ","focusin focusout keyup",r).validateDelegate("[type='radio'], [type='checkbox'], select, option","click",r);if(this.settings.invalidHandler){e(this.currentForm).bind("invalid-form.validate",this.settings.invalidHandler)}},form:function(){this.checkForm();e.extend(this.submitted,this.errorMap);this.invalid=e.extend({},this.errorMap);if(!this.valid()){e(this.currentForm).triggerHandler("invalid-form",[this])}this.showErrors();return this.valid()},checkForm:function(){this.prepareForm();for(var e=0,t=this.currentElements=this.elements();t[e];e++){if(this.findByName(t[e].name).length!=undefined&&this.findByName(t[e].name).length>1){for(var n=0;n<this.findByName(t[e].name).length;n++){this.check(this.findByName(t[e].name)[n])}}else{this.check(t[e])}}return this.valid()},element:function(t){t=this.validationTargetFor(this.clean(t));this.lastElement=t;this.prepareElement(t);this.currentElements=e(t);var n=this.check(t)!==false;if(n){delete this.invalid[t.name]}else{this.invalid[t.name]=true}if(!this.numberOfInvalids()){this.toHide=this.toHide.add(this.containers)}this.showErrors();return n},showErrors:function(t){if(t){e.extend(this.errorMap,t);this.errorList=[];for(var n in t){this.errorList.push({message:t[n],element:this.findByName(n)[0]})}this.successList=e.grep(this.successList,function(e){return!(e.name in t)})}if(this.settings.showErrors){this.settings.showErrors.call(this,this.errorMap,this.errorList)}else{this.defaultShowErrors()}},resetForm:function(){if(e.fn.resetForm){e(this.currentForm).resetForm()}this.submitted={};this.lastElement=null;this.prepareForm();this.hideErrors();this.elements().removeClass(this.settings.errorClass).removeData("previousValue")},numberOfInvalids:function(){return this.objectLength(this.invalid)},objectLength:function(e){var t=0;for(var n in e){t++}return t},hideErrors:function(){this.addWrapper(this.toHide).hide()},valid:function(){return this.size()===0},size:function(){return this.errorList.length},focusInvalid:function(){if(this.settings.focusInvalid){try{e(this.findLastActive()||this.errorList.length&&this.errorList[0].element||[]).filter(":visible").focus().trigger("focusin")}catch(t){}}},findLastActive:function(){var t=this.lastActive;return t&&e.grep(this.errorList,function(e){return e.element.name===t.name}).length===1&&t},elements:function(){var t=this,n={};return e(this.currentForm).find("input, select, textarea").not(":submit, :reset, :image, [disabled]").not(this.settings.ignore).filter(function(){if(!this.name&&t.settings.debug&&window.console){console.error("%o has no name assigned",this)}if(this.name in n||!t.objectLength(e(this).rules())){return false}n[this.name]=true;return true})},clean:function(t){return e(t)[0]},errors:function(){var t=this.settings.errorClass.replace(" ",".");return e(this.settings.errorElement+"."+t,this.errorContext)},reset:function(){this.successList=[];this.errorList=[];this.errorMap={};this.toShow=e([]);this.toHide=e([]);this.currentElements=e([])},prepareForm:function(){this.reset();this.toHide=this.errors().add(this.containers)},prepareElement:function(e){this.reset();this.toHide=this.errorsFor(e)},elementValue:function(t){var n=e(t).attr("type"),r=e(t).val();if(n==="radio"||n==="checkbox"){return e("input[name='"+e(t).attr("name")+"']:checked").val()}if(typeof r==="string"){return r.replace(/\r/g,"")}return r},check:function(t){t=this.validationTargetFor(this.clean(t));var n=e(t).rules();var r=false;var i=this.elementValue(t);var s;for(var o in n){var u={method:o,parameters:n[o]};try{s=e.validator.methods[o].call(this,i,t,u.parameters);if(s==="dependency-mismatch"){r=true;continue}r=false;if(s==="pending"){this.toHide=this.toHide.not(this.errorsFor(t));return}if(!s){this.formatAndAdd(t,u);return false}}catch(a){if(this.settings.debug&&window.console){console.log("Exception occurred when checking element "+t.id+", check the '"+u.method+"' method.",a)}throw a}}if(r){return}if(this.objectLength(n)){this.successList.push(t)}return true},customDataMessage:function(t,n){return e(t).data("msg-"+n.toLowerCase())||t.attributes&&e(t).attr("data-msg-"+n.toLowerCase())},customMessage:function(e,t){var n=this.settings.messages[e];return n&&(n.constructor===String?n:n[t])},findDefined:function(){for(var e=0;e<arguments.length;e++){if(arguments[e]!==undefined){return arguments[e]}}return undefined},defaultMessage:function(t,n){return this.findDefined(this.customMessage(t.name,n),this.customDataMessage(t,n),!this.settings.ignoreTitle&&t.title||undefined,e.validator.messages[n],"<strong>Warning: No message defined for "+t.name+"</strong>")},formatAndAdd:function(t,n){var r=this.defaultMessage(t,n.method),i=/\$?\{(\d+)\}/g;if(typeof r==="function"){r=r.call(this,n.parameters,t)}else if(i.test(r)){r=e.validator.format(r.replace(i,"{$1}"),n.parameters)}this.errorList.push({message:r,element:t});this.errorMap[t.name]=r;this.submitted[t.name]=r},addWrapper:function(e){if(this.settings.wrapper){e=e.add(e.parent(this.settings.wrapper))}return e},defaultShowErrors:function(){var e,t;for(e=0;this.errorList[e];e++){var n=this.errorList[e];if(this.settings.highlight){this.settings.highlight.call(this,n.element,this.settings.errorClass,this.settings.validClass)}this.showLabel(n.element,n.message)}if(this.errorList.length){this.toShow=this.toShow.add(this.containers)}if(this.settings.success){for(e=0;this.successList[e];e++){this.showLabel(this.successList[e])}}if(this.settings.unhighlight){for(e=0,t=this.validElements();t[e];e++){this.settings.unhighlight.call(this,t[e],this.settings.errorClass,this.settings.validClass)}}this.toHide=this.toHide.not(this.toShow);this.hideErrors();this.addWrapper(this.toShow).show()},validElements:function(){return this.currentElements.not(this.invalidElements())},invalidElements:function(){return e(this.errorList).map(function(){return this.element})},showLabel:function(t,n){var r=this.errorsFor(t);if(r.length){r.removeClass(this.settings.validClass).addClass(this.settings.errorClass);r.html(n)}else{r=e("<"+this.settings.errorElement+">").attr("for",this.idOrName(t)).addClass(this.settings.errorClass).html(n||"");if(this.settings.wrapper){r=r.hide().show().wrap("<"+this.settings.wrapper+"/>").parent()}if(!this.labelContainer.append(r).length){if(this.settings.errorPlacement){this.settings.errorPlacement(r,e(t))}else{r.insertAfter(t)}}}if(!n&&this.settings.success){r.text("");if(typeof this.settings.success==="string"){r.addClass(this.settings.success)}else{this.settings.success(r,t)}}this.toShow=this.toShow.add(r)},errorsFor:function(t){var n=this.idOrName(t);return this.errors().filter(function(){return e(this).attr("for")===n})},idOrName:function(e){return this.groups[e.name]||(this.checkable(e)?e.name:e.id||e.name)},validationTargetFor:function(e){if(this.checkable(e)){e=this.findByName(e.name).not(this.settings.ignore)[0]}return e},checkable:function(e){return/radio|checkbox/i.test(e.type)},findByName:function(t){return e(this.currentForm).find("[name='"+t+"']")},getLength:function(t,n){switch(n.nodeName.toLowerCase()){case"select":return e("option:selected",n).length;case"input":if(this.checkable(n)){return this.findByName(n.name).filter(":checked").length}}return t.length},depend:function(e,t){return this.dependTypes[typeof e]?this.dependTypes[typeof e](e,t):true},dependTypes:{"boolean":function(e,t){return e},string:function(t,n){return!!e(t,n.form).length},"function":function(e,t){return e(t)}},optional:function(t){var n=this.elementValue(t);return!e.validator.methods.required.call(this,n,t)&&"dependency-mismatch"},startRequest:function(e){if(!this.pending[e.name]){this.pendingRequest++;this.pending[e.name]=true}},stopRequest:function(t,n){this.pendingRequest--;if(this.pendingRequest<0){this.pendingRequest=0}delete this.pending[t.name];if(n&&this.pendingRequest===0&&this.formSubmitted&&this.form()){e(this.currentForm).submit();this.formSubmitted=false}else if(!n&&this.pendingRequest===0&&this.formSubmitted){e(this.currentForm).triggerHandler("invalid-form",[this]);this.formSubmitted=false}},previousValue:function(t){return e.data(t,"previousValue")||e.data(t,"previousValue",{old:null,valid:true,message:this.defaultMessage(t,"remote")})}},classRuleSettings:{required:{required:true},email:{email:true},url:{url:true},date:{date:true},dateISO:{dateISO:true},number:{number:true},digits:{digits:true},creditcard:{creditcard:true}},addClassRules:function(t,n){if(t.constructor===String){this.classRuleSettings[t]=n}else{e.extend(this.classRuleSettings,t)}},classRules:function(t){var n={};var r=e(t).attr("class");if(r){e.each(r.split(" "),function(){if(this in e.validator.classRuleSettings){e.extend(n,e.validator.classRuleSettings[this])}})}return n},attributeRules:function(t){var n={};var r=e(t);var i=r[0].getAttribute("type");for(var s in e.validator.methods){var o;if(s==="required"){o=r.get(0).getAttribute(s);if(o===""){o=true}o=!!o}else{o=r.attr(s)}if(/min|max/.test(s)&&(i===null||/number|range|text/.test(i))){o=Number(o)}if(o){n[s]=o}else if(i===s&&i!=="range"){n[s]=true}}if(n.maxlength&&/-1|2147483647|524288/.test(n.maxlength)){delete n.maxlength}return n},dataRules:function(t){var n,r,i={},s=e(t);for(n in e.validator.methods){r=s.data("rule-"+n.toLowerCase());if(r!==undefined){i[n]=r}}return i},staticRules:function(t){var n={};var r=e.data(t.form,"validator");if(r.settings.rules){n=e.validator.normalizeRule(r.settings.rules[t.name])||{}}return n},normalizeRules:function(t,n){e.each(t,function(r,i){if(i===false){delete t[r];return}if(i.param||i.depends){var s=true;switch(typeof i.depends){case"string":s=!!e(i.depends,n.form).length;break;case"function":s=i.depends.call(n,n);break}if(s){t[r]=i.param!==undefined?i.param:true}else{delete t[r]}}});e.each(t,function(r,i){t[r]=e.isFunction(i)?i(n):i});e.each(["minlength","maxlength"],function(){if(t[this]){t[this]=Number(t[this])}});e.each(["rangelength","range"],function(){var n;if(t[this]){if(e.isArray(t[this])){t[this]=[Number(t[this][0]),Number(t[this][1])]}else if(typeof t[this]==="string"){n=t[this].split(/[\s,]+/);t[this]=[Number(n[0]),Number(n[1])]}}});if(e.validator.autoCreateRanges){if(t.min&&t.max){t.range=[t.min,t.max];delete t.min;delete t.max}if(t.minlength&&t.maxlength){t.rangelength=[t.minlength,t.maxlength];delete t.minlength;delete t.maxlength}}return t},normalizeRule:function(t){if(typeof t==="string"){var n={};e.each(t.split(/\s/),function(){n[this]=true});t=n}return t},addMethod:function(t,n,r){e.validator.methods[t]=n;e.validator.messages[t]=r!==undefined?r:e.validator.messages[t];if(n.length<3){e.validator.addClassRules(t,e.validator.normalizeRule(t))}},methods:{required:function(t,n,r){if(!this.depend(r,n)){return"dependency-mismatch"}if(n.nodeName.toLowerCase()==="select"){var i=e(n).val();return i&&i.length>0}if(this.checkable(n)){return this.getLength(t,n)>0}return e.trim(t).length>0},email:function(e,t){return this.optional(t)||/^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))$/i.test(e)},url:function(e,t){return this.optional(t)||/^(https?|s?ftp):\/\/(((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:)*@)?(((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]))|((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?)(:\d*)?)(\/((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)+(\/(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)*)*)?)?(\?((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|[\uE000-\uF8FF]|\/|\?)*)?(#((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|\/|\?)*)?$/i.test(e)},date:function(e,t){return this.optional(t)||!/Invalid|NaN/.test((new Date(e)).toString())},dateISO:function(e,t){return this.optional(t)||/^\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}$/.test(e)},number:function(e,t){return this.optional(t)||/^-?(?:\d+|\d{1,3}(?:,\d{3})+)?(?:\.\d+)?$/.test(e)},digits:function(e,t){return this.optional(t)||/^\d+$/.test(e)},creditcard:function(e,t){if(this.optional(t)){return"dependency-mismatch"}if(/[^0-9 \-]+/.test(e)){return false}var n=0,r=0,i=false;e=e.replace(/\D/g,"");for(var s=e.length-1;s>=0;s--){var o=e.charAt(s);r=parseInt(o,10);if(i){if((r*=2)>9){r-=9}}n+=r;i=!i}return n%10===0},minlength:function(t,n,r){var i=e.isArray(t)?t.length:this.getLength(e.trim(t),n);return this.optional(n)||i>=r},maxlength:function(t,n,r){var i=e.isArray(t)?t.length:this.getLength(e.trim(t),n);return this.optional(n)||i<=r},rangelength:function(t,n,r){var i=e.isArray(t)?t.length:this.getLength(e.trim(t),n);return this.optional(n)||i>=r[0]&&i<=r[1]},min:function(e,t,n){return this.optional(t)||e>=n},max:function(e,t,n){return this.optional(t)||e<=n},range:function(e,t,n){return this.optional(t)||e>=n[0]&&e<=n[1]},equalTo:function(t,n,r){var i=e(r);if(this.settings.onfocusout){i.unbind(".validate-equalTo").bind("blur.validate-equalTo",function(){e(n).valid()})}return t===i.val()},remote:function(t,n,r){if(this.optional(n)){return"dependency-mismatch"}var i=this.previousValue(n);if(!this.settings.messages[n.name]){this.settings.messages[n.name]={}}i.originalMessage=this.settings.messages[n.name].remote;this.settings.messages[n.name].remote=i.message;r=typeof r==="string"&&{url:r}||r;if(i.old===t){return i.valid}i.old=t;var s=this;this.startRequest(n);var o={};o[n.name]=t;e.ajax(e.extend(true,{url:r,mode:"abort",port:"validate"+n.name,dataType:"json",data:o,success:function(r){s.settings.messages[n.name].remote=i.originalMessage;var o=r===true||r==="true";if(o){var u=s.formSubmitted;s.prepareElement(n);s.formSubmitted=u;s.successList.push(n);delete s.invalid[n.name];s.showErrors()}else{var a={};var f=r||s.defaultMessage(n,"remote");a[n.name]=i.message=e.isFunction(f)?f(t):f;s.invalid[n.name]=true;s.showErrors(a)}i.valid=o;s.stopRequest(n,o)}},r));return"pending"}}});e.format=e.validator.format})(jQuery);(function(e){var t={};if(e.ajaxPrefilter){e.ajaxPrefilter(function(e,n,r){var i=e.port;if(e.mode==="abort"){if(t[i]){t[i].abort()}t[i]=r}})}else{var n=e.ajax;e.ajax=function(r){var i=("mode"in r?r:e.ajaxSettings).mode,s=("port"in r?r:e.ajaxSettings).port;if(i==="abort"){if(t[s]){t[s].abort()}t[s]=n.apply(this,arguments);return t[s]}return n.apply(this,arguments)}}})(jQuery);(function(e){e.extend(e.fn,{validateDelegate:function(t,n,r){return this.bind(n,function(n){var i=e(n.target);if(i.is(t)){return r.apply(i,arguments)}})}})})(jQuery)
/* form validation*/

/* jquery select */
!function(a){"use strict";a.fn.selectOrDie=function(b){var f,g,c={customID:null,customClass:"",placeholder:null,placeholderOption:!1,prefix:null,cycle:!1,stripEmpty:!1,links:!1,linksExternal:!1,size:0,tabIndex:0,onChange:a.noop},d={},e=!1,h={initSoD:function(b){return d=a.extend({},c,b),this.each(function(){if(a(this).parent().hasClass("sod_select"))console.log("Select or Die: It looks like the SoD already exists");else{var u,v,w,b=a(this),c=b.data("custom-id")?b.data("custom-id"):d.customID,e=b.data("custom-class")?b.data("custom-class"):d.customClass,f=b.data("prefix")?b.data("prefix"):d.prefix,g=b.data("placeholder")?b.data("placeholder"):d.placeholder,i=b.data("placeholder-option")?b.data("placeholder-option"):d.placeholderOption,j=b.data("cycle")?b.data("cycle"):d.cycle,k=b.data("links")?b.data("links"):d.links,l=b.data("links-external")?b.data("links-external"):d.linksExternal,m=parseInt(b.data("size"))?b.data("size"):d.size,n=parseInt(b.data("tabindex"))?b.data("tabindex"):d.tabIndex?d.tabIndex:b.attr("tabindex")?b.attr("tabindex"):d.tabIndex,o=b.data("strip-empty")?b.data("strip-empty"):d.stripEmpty,p=b.prop("title")?b.prop("title"):null,q=b.is(":disabled")?" disabled":"",r="",s="",t=0;f&&(r='<span class="sod_prefix">'+f+"</span> "),s+=g&&!f?'<span class="sod_label sod_placeholder">'+g+"</span>":'<span class="sod_label">'+r+"</span>",u=a("<span/>",{id:c,"class":"sod_select "+e+q,title:p,tabindex:n,html:s,"data-cycle":j,"data-links":k,"data-links-external":l,"data-placeholder":g,"data-placeholder-option":i,"data-prefix":f,"data-filter":""}).insertAfter(this),h.isTouch()&&u.addClass("touch"),v=a("<span/>",{"class":"sod_list_wrapper"}).appendTo(u),w=a("<span/>",{"class":"sod_list"}).appendTo(v),a("option, optgroup",b).each(function(b){var c=a(this);o&&!a.trim(c.text())?c.remove():0===b&&i&&!r?h.populateSoD(c,w,u,!0):h.populateSoD(c,w,u,!1)}),m&&(v.show(),a(".sod_option:lt("+m+")",w).each(function(){t+=a(this).outerHeight()}),v.removeAttr("style"),w.css({"max-height":t})),b.appendTo(u),u.on("focusin",h.focusSod).on("click",h.triggerSod).on("click",".sod_option",h.optionClick).on("mousemove",".sod_option",h.optionHover).on("keydown",h.keyboardUse),b.on("change",h.selectChange),a(document).on("click","label[for='"+b.attr("id")+"']",function(a){a.preventDefault(),u.focus()})}})},populateSoD:function(b,c,d,e){var f=d.data("placeholder"),g=d.data("placeholder-option"),h=d.data("prefix"),i=d.find(".sod_label"),j=b.parent(),k=b.text(),l=b.val(),m=b.data("custom-id")?b.data("custom-id"):null,n=b.data("custom-class")?b.data("custom-class"):"",o=b.is(":disabled")?" disabled ":"",p=b.is(":selected")?" selected active ":"",q=b.data("link")?" link ":"",r=b.data("link-external")?" linkexternal":"",s=b.prop("label");b.is("option")?(a("<span/>",{"class":"sod_option "+n+o+p+q+r,id:m,title:k,html:k,"data-value":l}).appendTo(c),e&&!h?(d.data("label",k),d.data("placeholder",k),b.prop("disabled",!0),c.find(".sod_option:last").addClass("is-placeholder disabled"),p&&i.addClass("sod_placeholder")):p&&f&&!g&&!h?d.data("label",f):p&&d.data("label",k),(p&&!f||p&&g||p&&h)&&i.append(k),j.is("optgroup")&&(c.find(".sod_option:last").addClass("groupchild"),j.is(":disabled")&&c.find(".sod_option:last").addClass("disabled"))):a("<span/>",{"class":"sod_option optgroup "+o,title:s,html:s,"data-label":s}).appendTo(c)},focusSod:function(){var b=a(this);b.hasClass("disabled")?h.blurSod(b):(h.blurSod(a(".sod_select.focus").not(b)),b.addClass("focus"),a("html").on("click.sodBlur",function(){h.blurSod(b)}))},triggerSod:function(b){b.stopPropagation();var c=a(this),d=c.find(".sod_list"),e=c.data("placeholder"),f=c.find(".active"),i=c.find(".selected");c.hasClass("disabled")||c.hasClass("open")||c.hasClass("touch")?(clearTimeout(g),c.removeClass("open"),e&&(c.find(".sod_label").get(0).lastChild.nodeValue=f.text())):(c.addClass("open"),e&&!c.data("prefix")&&c.find(".sod_label").addClass("sod_placeholder").html(e),h.listScroll(d,i),h.checkViewport(c,d))},keyboardUse:function(b){var l,m,n,c=a(this),d=c.find(".sod_list"),g=c.find(".sod_option"),i=c.find(".sod_label"),j=c.data("cycle"),k=g.filter(".active");return b.which>36&&b.which<41?(37===b.which||38===b.which?(m=k.prevAll(":not('.disabled, .optgroup')").first(),n=g.not(".disabled, .optgroup").last()):(39===b.which||40===b.which)&&(m=k.nextAll(":not('.disabled, .optgroup')").first(),n=g.not(".disabled, .optgroup").first()),!m.hasClass("sod_option")&&j&&(m=n),(m.hasClass("sod_option")||j)&&(k.removeClass("active"),m.addClass("active"),i.get(0).lastChild.nodeValue=m.text(),h.listScroll(d,m),c.hasClass("open")||(e=!0)),!1):(13===b.which||32===b.which&&c.hasClass("open")&&(" "===c.data("filter")[0]||""===c.data("filter"))?(b.preventDefault(),k.click()):32!==b.which||c.hasClass("open")||" "!==c.data("filter")[0]&&""!==c.data("filter")?27===b.which&&h.blurSod(c):(b.preventDefault(),e=!1,c.click()),0!==b.which&&(clearTimeout(f),c.data("filter",c.data("filter")+String.fromCharCode(b.which)),l=g.filter(function(){return 0===a(this).text().toLowerCase().indexOf(c.data("filter").toLowerCase())}).not(".disabled, .optgroup").first(),l.length&&(k.removeClass("active"),l.addClass("active"),h.listScroll(d,l),i.get(0).lastChild.nodeValue=l.text(),c.hasClass("open")||(e=!0)),f=setTimeout(function(){c.data("filter","")},500)),void 0)},optionHover:function(){var b=a(this);b.hasClass("disabled")||b.hasClass("optgroup")||b.siblings().removeClass("active").end().addClass("active")},optionClick:function(b){b.stopPropagation();var c=a(this),d=c.closest(".sod_select"),e=c.hasClass("disabled"),f=c.hasClass("optgroup"),h=d.find(".sod_option:not('.optgroup')").index(this);d.hasClass("touch")||(e||f||(d.find(".selected, .sod_placeholder").removeClass("selected sod_placeholder"),c.addClass("selected"),d.find("select option")[h].selected=!0,d.find("select").change()),clearTimeout(g),d.removeClass("open"))},selectChange:function(){var b=a(this),c=b.find(":selected"),e=c.text(),f=b.closest(".sod_select");f.find(".sod_label").get(0).lastChild.nodeValue=e,f.data("label",e),d.onChange.call(this),!f.data("links")&&!c.data("link")||c.data("link-external")?(f.data("links-external")||c.data("link-external"))&&window.open(c.val(),"_blank"):window.location.href=c.val()},blurSod:function(b){if(a("body").find(b).length){var c=b.data("label"),d=b.data("placeholder"),f=b.find(".active"),h=b.find(".selected"),i=!1;clearTimeout(g),e&&!f.hasClass("selected")?(f.click(),i=!0):f.hasClass("selected")||(f.removeClass("active"),h.addClass("active")),!i&&d?b.find(".sod_label").get(0).lastChild.nodeValue=h.text():i||(b.find(".sod_label").get(0).lastChild.nodeValue=c),e=!1,b.removeClass("open focus"),b.blur(),a("html").off(".sodBlur")}},checkViewport:function(b,c){var d=b[0].getBoundingClientRect(),e=c.outerHeight();d.bottom+e+10>a(window).height()&&d.top-e>10?b.addClass("above"):b.removeClass("above"),g=setTimeout(function(){h.checkViewport(b,c)},200)},listScroll:function(a,b){var c=a[0].getBoundingClientRect(),d=b[0].getBoundingClientRect();c.top>d.top?a.scrollTop(a.scrollTop()-c.top+d.top):c.bottom<d.bottom&&a.scrollTop(a.scrollTop()-c.bottom+d.bottom)},isTouch:function(){return"ontouchstart"in window||navigator.MaxTouchPoints>0||navigator.msMaxTouchPoints>0}},i={destroy:function(){return this.each(function(){var b=a(this),c=b.parent();c.hasClass("sod_select")?(b.off("change"),c.find("span").remove(),b.unwrap()):console.log("Select or Die: There's no SoD to destroy")})},update:function(){return this.each(function(){var b=a(this),c=b.parent(),d=c.find(".sod_list:first");c.hasClass("sod_select")?(d.empty(),c.find(".sod_label").get(0).lastChild.nodeValue="",b.is(":disabled")&&c.addClass("disabled"),a("option, optgroup",b).each(function(){h.populateSoD(a(this),d,c)})):console.log("Select or Die: There's no SoD to update")})},disable:function(b){return this.each(function(){var c=a(this),d=c.parent();d.hasClass("sod_select")?"undefined"!=typeof b?(d.find(".sod_list:first .sod_option[data-value='"+b+"']").addClass("disabled"),d.find(".sod_list:first .sod_option[data-label='"+b+"']").nextUntil(":not(.groupchild)").addClass("disabled"),a("option[value='"+b+"'], optgroup[label='"+b+"']",this).prop("disabled",!0)):d.hasClass("sod_select")&&(d.addClass("disabled"),c.prop("disabled",!0)):console.log("Select or Die: There's no SoD to disable")})},enable:function(b){return this.each(function(){var c=a(this),d=c.parent();d.hasClass("sod_select")?"undefined"!=typeof b?(d.find(".sod_list:first .sod_option[data-value='"+b+"']").removeClass("disabled"),d.find(".sod_list:first .sod_option[data-label='"+b+"']").nextUntil(":not(.groupchild)").removeClass("disabled"),a("option[value='"+b+"'], optgroup[label='"+b+"']",this).prop("disabled",!1)):d.hasClass("sod_select")&&(d.removeClass("disabled"),c.prop("disabled",!1)):console.log("Select or Die: There's no SoD to enable")})}};return i[b]?i[b].apply(this,Array.prototype.slice.call(arguments,1)):"object"!=typeof b&&b?(a.error('Select or Die: Oh no! No such method "'+b+'" for the SoD instance'),void 0):h.initSoD.apply(this,arguments)}}(jQuery);
/* jquery select */

/*custom scroll*/
"use strict";(function(e){"function"==typeof define&&define.amd?define(["jquery"],e):e(jQuery)})(function(e){var r={wheelSpeed:10,wheelPropagation:!1,minScrollbarLength:null,useBothWheelAxes:!1,useKeyboard:!0,suppressScrollX:!1,suppressScrollY:!1,scrollXMarginOffset:0,scrollYMarginOffset:0};e.fn.perfectScrollbar=function(o,t){return this.each(function(){var l=e.extend(!0,{},r),n=e(this);if("object"==typeof o?e.extend(!0,l,o):t=o,"update"===t)return n.data("perfect-scrollbar-update")&&n.data("perfect-scrollbar-update")(),n;if("destroy"===t)return n.data("perfect-scrollbar-destroy")&&n.data("perfect-scrollbar-destroy")(),n;if(n.data("perfect-scrollbar"))return n.data("perfect-scrollbar");n.addClass("ps-container");var s,c,a,i,p,f,u,d,b,h,v=e("<div class='ps-scrollbar-x-rail'></div>").appendTo(n),g=e("<div class='ps-scrollbar-y-rail'></div>").appendTo(n),m=e("<div class='ps-scrollbar-x'></div>").appendTo(v),w=e("<div class='ps-scrollbar-y'></div>").appendTo(g),T=parseInt(v.css("bottom"),10),L=parseInt(g.css("right"),10),y=function(){var e=parseInt(h*(f-i)/(i-b),10);n.scrollTop(e),v.css({bottom:T-e})},S=function(){var e=parseInt(d*(p-a)/(a-u),10);n.scrollLeft(e),g.css({right:L-e})},I=function(e){return l.minScrollbarLength&&(e=Math.max(e,l.minScrollbarLength)),e},X=function(){v.css({left:n.scrollLeft(),bottom:T-n.scrollTop(),width:a,display:l.suppressScrollX?"none":"inherit"}),g.css({top:n.scrollTop(),right:L-n.scrollLeft(),height:i,display:l.suppressScrollY?"none":"inherit"}),m.css({left:d,width:u}),w.css({top:h,height:b})},D=function(){a=n.width(),i=n.height(),p=n.prop("scrollWidth"),f=n.prop("scrollHeight"),!l.suppressScrollX&&p>a+l.scrollXMarginOffset?(s=!0,u=I(parseInt(a*a/p,10)),d=parseInt(n.scrollLeft()*(a-u)/(p-a),10)):(s=!1,u=0,d=0,n.scrollLeft(0)),!l.suppressScrollY&&f>i+l.scrollYMarginOffset?(c=!0,b=I(parseInt(i*i/f,10)),h=parseInt(n.scrollTop()*(i-b)/(f-i),10)):(c=!1,b=0,h=0,n.scrollTop(0)),h>=i-b&&(h=i-b),d>=a-u&&(d=a-u),X()},Y=function(e,r){var o=e+r,t=a-u;d=0>o?0:o>t?t:o,v.css({left:n.scrollLeft()}),m.css({left:d})},x=function(e,r){var o=e+r,t=i-b;h=0>o?0:o>t?t:o,g.css({top:n.scrollTop()}),w.css({top:h})},C=function(){var r,o;m.bind("mousedown.perfect-scrollbar",function(e){o=e.pageX,r=m.position().left,v.addClass("in-scrolling"),e.stopPropagation(),e.preventDefault()}),e(document).bind("mousemove.perfect-scrollbar",function(e){v.hasClass("in-scrolling")&&(S(),Y(r,e.pageX-o),e.stopPropagation(),e.preventDefault())}),e(document).bind("mouseup.perfect-scrollbar",function(){v.hasClass("in-scrolling")&&v.removeClass("in-scrolling")}),r=o=null},P=function(){var r,o;w.bind("mousedown.perfect-scrollbar",function(e){o=e.pageY,r=w.position().top,g.addClass("in-scrolling"),e.stopPropagation(),e.preventDefault()}),e(document).bind("mousemove.perfect-scrollbar",function(e){g.hasClass("in-scrolling")&&(y(),x(r,e.pageY-o),e.stopPropagation(),e.preventDefault())}),e(document).bind("mouseup.perfect-scrollbar",function(){g.hasClass("in-scrolling")&&g.removeClass("in-scrolling")}),r=o=null},k=function(){var e=function(e,r){var o=n.scrollTop();if(0===o&&r>0&&0===e)return!l.wheelPropagation;if(o>=f-i&&0>r&&0===e)return!l.wheelPropagation;var t=n.scrollLeft();return 0===t&&0>e&&0===r?!l.wheelPropagation:t>=p-a&&e>0&&0===r?!l.wheelPropagation:!0},r=!1;n.bind("mousewheel.perfect-scrollbar",function(o,t,a,i){l.useBothWheelAxes?c&&!s?i?n.scrollTop(n.scrollTop()-i*l.wheelSpeed):n.scrollTop(n.scrollTop()+a*l.wheelSpeed):s&&!c&&(a?n.scrollLeft(n.scrollLeft()+a*l.wheelSpeed):n.scrollLeft(n.scrollLeft()-i*l.wheelSpeed)):(n.scrollTop(n.scrollTop()-i*l.wheelSpeed),n.scrollLeft(n.scrollLeft()+a*l.wheelSpeed)),D(),r=e(a,i),r&&o.preventDefault()}),n.bind("MozMousePixelScroll.perfect-scrollbar",function(e){r&&e.preventDefault()})},M=function(){var r=function(e,r){var o=n.scrollTop();if(0===o&&r>0&&0===e)return!1;if(o>=f-i&&0>r&&0===e)return!1;var t=n.scrollLeft();return 0===t&&0>e&&0===r?!1:t>=p-a&&e>0&&0===r?!1:!0},o=!1;n.bind("mouseenter.perfect-scrollbar",function(){o=!0}),n.bind("mouseleave.perfect-scrollbar",function(){o=!1});var t=!1;e(document).bind("keydown.perfect-scrollbar",function(e){if(o){var s=0,c=0;switch(e.which){case 37:s=-3;break;case 38:c=3;break;case 39:s=3;break;case 40:c=-3;break;default:return}n.scrollTop(n.scrollTop()-c*l.wheelSpeed),n.scrollLeft(n.scrollLeft()+s*l.wheelSpeed),D(),t=r(s,c),t&&e.preventDefault()}})},O=function(){var e=function(e){e.stopPropagation()};w.bind("click.perfect-scrollbar",e),g.bind("click.perfect-scrollbar",function(e){var r=parseInt(b/2,10),o=e.pageY-g.offset().top-r,t=i-b,l=o/t;0>l?l=0:l>1&&(l=1),n.scrollTop((f-i)*l),D()}),m.bind("click.perfect-scrollbar",e),v.bind("click.perfect-scrollbar",function(e){var r=parseInt(u/2,10),o=e.pageX-v.offset().left-r,t=a-u,l=o/t;0>l?l=0:l>1&&(l=1),n.scrollLeft((p-a)*l),D()})},E=function(){var r=function(e,r){n.scrollTop(n.scrollTop()-r),n.scrollLeft(n.scrollLeft()-e),D()},o={},t=0,l={},s=null,c=!1;e(window).bind("touchstart.perfect-scrollbar",function(){c=!0}),e(window).bind("touchend.perfect-scrollbar",function(){c=!1}),n.bind("touchstart.perfect-scrollbar",function(e){var r=e.originalEvent.targetTouches[0];o.pageX=r.pageX,o.pageY=r.pageY,t=(new Date).getTime(),null!==s&&clearInterval(s),e.stopPropagation()}),n.bind("touchmove.perfect-scrollbar",function(e){if(!c&&1===e.originalEvent.targetTouches.length){var n=e.originalEvent.targetTouches[0],s={};s.pageX=n.pageX,s.pageY=n.pageY;var a=s.pageX-o.pageX,i=s.pageY-o.pageY;r(a,i),o=s;var p=(new Date).getTime();l.x=a/(p-t),l.y=i/(p-t),t=p,e.preventDefault()}}),n.bind("touchend.perfect-scrollbar",function(){clearInterval(s),s=setInterval(function(){return.01>Math.abs(l.x)&&.01>Math.abs(l.y)?(clearInterval(s),void 0):(r(30*l.x,30*l.y),l.x*=.8,l.y*=.8,void 0)},10)})},A=function(){n.unbind(".perfect-scrollbar"),e(window).unbind(".perfect-scrollbar"),e(document).unbind(".perfect-scrollbar"),n.data("perfect-scrollbar",null),n.data("perfect-scrollbar-update",null),n.data("perfect-scrollbar-destroy",null),m.remove(),w.remove(),v.remove(),g.remove(),m=w=a=i=p=f=u=d=T=b=h=L=null},j=function(r){n.addClass("ie").addClass("ie"+r);var o=function(){var r=function(){e(this).addClass("hover")},o=function(){e(this).removeClass("hover")};n.bind("mouseenter.perfect-scrollbar",r).bind("mouseleave.perfect-scrollbar",o),v.bind("mouseenter.perfect-scrollbar",r).bind("mouseleave.perfect-scrollbar",o),g.bind("mouseenter.perfect-scrollbar",r).bind("mouseleave.perfect-scrollbar",o),m.bind("mouseenter.perfect-scrollbar",r).bind("mouseleave.perfect-scrollbar",o),w.bind("mouseenter.perfect-scrollbar",r).bind("mouseleave.perfect-scrollbar",o)},t=function(){X=function(){m.css({left:d+n.scrollLeft(),bottom:T,width:u}),w.css({top:h+n.scrollTop(),right:L,height:b}),m.hide().show(),w.hide().show()},y=function(){var e=parseInt(h*f/i,10);n.scrollTop(e),m.css({bottom:T}),m.hide().show()},S=function(){var e=parseInt(d*p/a,10);n.scrollLeft(e),w.hide().show()}};6===r&&(o(),t())},W="ontouchstart"in window||window.DocumentTouch&&document instanceof window.DocumentTouch,H=function(){var e=navigator.userAgent.toLowerCase().match(/(msie) ([\w.]+)/);e&&"msie"===e[1]&&j(parseInt(e[2],10)),D(),C(),P(),O(),W&&E(),n.mousewheel&&k(),l.useKeyboard&&M(),n.data("perfect-scrollbar",n),n.data("perfect-scrollbar-update",D),n.data("perfect-scrollbar-destroy",A)};return H(),n})}}),function(e){function r(r){var o=r||window.event,t=[].slice.call(arguments,1),l=0,n=0,s=0;return r=e.event.fix(o),r.type="mousewheel",o.wheelDelta&&(l=o.wheelDelta/120),o.detail&&(l=-o.detail/3),s=l,void 0!==o.axis&&o.axis===o.HORIZONTAL_AXIS&&(s=0,n=-1*l),void 0!==o.wheelDeltaY&&(s=o.wheelDeltaY/120),void 0!==o.wheelDeltaX&&(n=-1*o.wheelDeltaX/120),t.unshift(r,l,n,s),(e.event.dispatch||e.event.handle).apply(this,t)}var o=["DOMMouseScroll","mousewheel"];if(e.event.fixHooks)for(var t=o.length;t;)e.event.fixHooks[o[--t]]=e.event.mouseHooks;e.event.special.mousewheel={setup:function(){if(this.addEventListener)for(var e=o.length;e;)this.addEventListener(o[--e],r,!1);else this.onmousewheel=r},teardown:function(){if(this.removeEventListener)for(var e=o.length;e;)this.removeEventListener(o[--e],r,!1);else this.onmousewheel=null}},e.fn.extend({mousewheel:function(e){return e?this.bind("mousewheel",e):this.trigger("mousewheel")},unmousewheel:function(e){return this.unbind("mousewheel",e)}})}(jQuery);
"use strict";(function(e){"function"==typeof define&&define.amd?define(["jquery"],e):e(jQuery)})(function(e){var r={wheelSpeed:10,wheelPropagation:!1,minScrollbarLength:null,useBothWheelAxes:!1,useKeyboard:!0,suppressScrollX:!1,suppressScrollY:!1,scrollXMarginOffset:0,scrollYMarginOffset:0};e.fn.perfectScrollbar=function(o,l){return this.each(function(){var t=e.extend(!0,{},r),s=e(this);if("object"==typeof o?e.extend(!0,t,o):l=o,"update"===l)return s.data("perfect-scrollbar-update")&&s.data("perfect-scrollbar-update")(),s;if("destroy"===l)return s.data("perfect-scrollbar-destroy")&&s.data("perfect-scrollbar-destroy")(),s;if(s.data("perfect-scrollbar"))return s.data("perfect-scrollbar");s.addClass("ps-container");var n,c,a,i,p,f,u,d,b,h,v=e("<div class='ps-scrollbar-x-rail'></div>").appendTo(s),g=e("<div class='ps-scrollbar-y-rail'></div>").appendTo(s),m=e("<div class='ps-scrollbar-x'></div>").appendTo(v),w=e("<div class='ps-scrollbar-y'></div>").appendTo(g),T=parseInt(v.css("bottom"),10),L=parseInt(g.css("right"),10),y=function(){var e=parseInt(h*(f-i)/(i-b),10);s.scrollTop(e),v.css({bottom:T-e})},S=function(){var e=parseInt(d*(p-a)/(a-u),10);s.scrollLeft(e),g.css({right:L-e})},I=function(e){return t.minScrollbarLength&&(e=Math.max(e,t.minScrollbarLength)),e},C=function(){v.css({left:s.scrollLeft(),bottom:T-s.scrollTop(),width:a,display:t.suppressScrollX?"none":"inherit"}),g.css({top:s.scrollTop(),right:L-s.scrollLeft(),height:i,display:t.suppressScrollY?"none":"inherit"}),m.css({left:d,width:u}),w.css({top:h,height:b})},X=function(){a=s.width(),i=s.height(),p=s.prop("scrollWidth"),f=s.prop("scrollHeight"),!t.suppressScrollX&&p>a+t.scrollXMarginOffset?(n=!0,u=I(parseInt(a*a/p,10)),d=parseInt(s.scrollLeft()*(a-u)/(p-a),10)):(n=!1,u=0,d=0,s.scrollLeft(0)),!t.suppressScrollY&&f>i+t.scrollYMarginOffset?(c=!0,b=I(parseInt(i*i/f,10)),h=parseInt(s.scrollTop()*(i-b)/(f-i),10)):(c=!1,b=0,h=0,s.scrollTop(0)),h>=i-b&&(h=i-b),d>=a-u&&(d=a-u),C()},Y=function(e,r){var o=e+r,l=a-u;d=0>o?0:o>l?l:o,v.css({left:s.scrollLeft()}),m.css({left:d})},x=function(e,r){var o=e+r,l=i-b;h=0>o?0:o>l?l:o,g.css({top:s.scrollTop()}),w.css({top:h})},D=function(){var r,o;m.bind("mousedown.perfect-scrollbar",function(e){o=e.pageX,r=m.position().left,v.addClass("in-scrolling"),e.stopPropagation(),e.preventDefault()}),e(document).bind("mousemove.perfect-scrollbar",function(e){v.hasClass("in-scrolling")&&(S(),Y(r,e.pageX-o),e.stopPropagation(),e.preventDefault())}),e(document).bind("mouseup.perfect-scrollbar",function(){v.hasClass("in-scrolling")&&v.removeClass("in-scrolling")}),r=o=null},P=function(){var r,o;w.bind("mousedown.perfect-scrollbar",function(e){o=e.pageY,r=w.position().top,g.addClass("in-scrolling"),e.stopPropagation(),e.preventDefault()}),e(document).bind("mousemove.perfect-scrollbar",function(e){g.hasClass("in-scrolling")&&(y(),x(r,e.pageY-o),e.stopPropagation(),e.preventDefault())}),e(document).bind("mouseup.perfect-scrollbar",function(){g.hasClass("in-scrolling")&&g.removeClass("in-scrolling")}),r=o=null},k=function(){var e=function(e,r){var o=s.scrollTop();if(0===o&&r>0&&0===e)return!t.wheelPropagation;if(o>=f-i&&0>r&&0===e)return!t.wheelPropagation;var l=s.scrollLeft();return 0===l&&0>e&&0===r?!t.wheelPropagation:l>=p-a&&e>0&&0===r?!t.wheelPropagation:!0},r=!1;s.bind("mousewheel.perfect-scrollbar",function(o,l,a,i){t.useBothWheelAxes?c&&!n?i?s.scrollTop(s.scrollTop()-i*t.wheelSpeed):s.scrollTop(s.scrollTop()+a*t.wheelSpeed):n&&!c&&(a?s.scrollLeft(s.scrollLeft()+a*t.wheelSpeed):s.scrollLeft(s.scrollLeft()-i*t.wheelSpeed)):(s.scrollTop(s.scrollTop()-i*t.wheelSpeed),s.scrollLeft(s.scrollLeft()+a*t.wheelSpeed)),X(),r=e(a,i),r&&o.preventDefault()}),s.bind("MozMousePixelScroll.perfect-scrollbar",function(e){r&&e.preventDefault()})},M=function(){var r=function(e,r){var o=s.scrollTop();if(0===o&&r>0&&0===e)return!1;if(o>=f-i&&0>r&&0===e)return!1;var l=s.scrollLeft();return 0===l&&0>e&&0===r?!1:l>=p-a&&e>0&&0===r?!1:!0},o=!1;s.bind("mouseenter.perfect-scrollbar",function(){o=!0}),s.bind("mouseleave.perfect-scrollbar",function(){o=!1});var l=!1;e(document).bind("keydown.perfect-scrollbar",function(e){if(o){var n=0,c=0;switch(e.which){case 37:n=-3;break;case 38:c=3;break;case 39:n=3;break;case 40:c=-3;break;default:return}s.scrollTop(s.scrollTop()-c*t.wheelSpeed),s.scrollLeft(s.scrollLeft()+n*t.wheelSpeed),X(),l=r(n,c),l&&e.preventDefault()}})},O=function(){var e=function(e){e.stopPropagation()};w.bind("click.perfect-scrollbar",e),g.bind("click.perfect-scrollbar",function(e){var r=parseInt(b/2,10),o=e.pageY-g.offset().top-r,l=i-b,t=o/l;0>t?t=0:t>1&&(t=1),s.scrollTop((f-i)*t),X()}),m.bind("click.perfect-scrollbar",e),v.bind("click.perfect-scrollbar",function(e){var r=parseInt(u/2,10),o=e.pageX-v.offset().left-r,l=a-u,t=o/l;0>t?t=0:t>1&&(t=1),s.scrollLeft((p-a)*t),X()})},j=function(){var r=function(e,r){s.scrollTop(s.scrollTop()-r),s.scrollLeft(s.scrollLeft()-e),X()},o={},l=0,t={},n=null,c=!1;e(window).bind("touchstart.perfect-scrollbar",function(){c=!0}),e(window).bind("touchend.perfect-scrollbar",function(){c=!1}),s.bind("touchstart.perfect-scrollbar",function(e){var r=e.originalEvent.targetTouches[0];o.pageX=r.pageX,o.pageY=r.pageY,l=(new Date).getTime(),null!==n&&clearInterval(n),e.stopPropagation()}),s.bind("touchmove.perfect-scrollbar",function(e){if(!c&&1===e.originalEvent.targetTouches.length){var s=e.originalEvent.targetTouches[0],n={};n.pageX=s.pageX,n.pageY=s.pageY;var a=n.pageX-o.pageX,i=n.pageY-o.pageY;r(a,i),o=n;var p=(new Date).getTime();t.x=a/(p-l),t.y=i/(p-l),l=p,e.preventDefault()}}),s.bind("touchend.perfect-scrollbar",function(){clearInterval(n),n=setInterval(function(){return.01>Math.abs(t.x)&&.01>Math.abs(t.y)?(clearInterval(n),void 0):(r(30*t.x,30*t.y),t.x*=.8,t.y*=.8,void 0)},10)})},A=function(){s.unbind(".perfect-scrollbar"),e(window).unbind(".perfect-scrollbar"),e(document).unbind(".perfect-scrollbar"),s.data("perfect-scrollbar",null),s.data("perfect-scrollbar-update",null),s.data("perfect-scrollbar-destroy",null),m.remove(),w.remove(),v.remove(),g.remove(),m=w=a=i=p=f=u=d=T=b=h=L=null},E=function(r){s.addClass("ie").addClass("ie"+r);var o=function(){var r=function(){e(this).addClass("hover")},o=function(){e(this).removeClass("hover")};s.bind("mouseenter.perfect-scrollbar",r).bind("mouseleave.perfect-scrollbar",o),v.bind("mouseenter.perfect-scrollbar",r).bind("mouseleave.perfect-scrollbar",o),g.bind("mouseenter.perfect-scrollbar",r).bind("mouseleave.perfect-scrollbar",o),m.bind("mouseenter.perfect-scrollbar",r).bind("mouseleave.perfect-scrollbar",o),w.bind("mouseenter.perfect-scrollbar",r).bind("mouseleave.perfect-scrollbar",o)},l=function(){C=function(){m.css({left:d+s.scrollLeft(),bottom:T,width:u}),w.css({top:h+s.scrollTop(),right:L,height:b}),m.hide().show(),w.hide().show()},y=function(){var e=parseInt(h*f/i,10);s.scrollTop(e),m.css({bottom:T}),m.hide().show()},S=function(){var e=parseInt(d*p/a,10);s.scrollLeft(e),w.hide().show()}};6===r&&(o(),l())},W="ontouchstart"in window||window.DocumentTouch&&document instanceof window.DocumentTouch,B=function(){var e=navigator.userAgent.toLowerCase().match(/(msie) ([\w.]+)/);e&&"msie"===e[1]&&E(parseInt(e[2],10)),X(),D(),P(),O(),W&&j(),s.mousewheel&&k(),t.useKeyboard&&M(),s.data("perfect-scrollbar",s),s.data("perfect-scrollbar-update",X),s.data("perfect-scrollbar-destroy",A)};return B(),s})}});
/*custom scroll*/

/*custom checkbox and radio*/
!function(e){e.fn.checkBo=function(c){return c=e.extend({},{checkAllButton:null,checkAllTarget:null,checkAllTextDefault:null,checkAllTextToggle:null},c),this.each(function(){function n(e){this.input=e}function t(){var c=e(this).is(":checked");e(this).closest("label").toggleClass("checked",c)}function i(e,c,n){e.text(e.parent(d).hasClass("checked")?n:c)}function l(c){var n=c.attr("data-show");c=c.attr("data-hide"),e(n).removeClass("is-hidden"),e(c).addClass("is-hidden")}var a=e(this),d=a.find(".cb-checkbox"),h=a.find(".cb-radio"),o=d.find("input:checkbox"),s=h.find("input:radio");o.wrap('<span class="cb-inner"><i></i></span>'),s.wrap('<span class="cb-inner"><i></i></span>');var f=new n("input:checkbox"),k=new n("input:radio");if(n.prototype.checkbox=function(e){var c=e.find(this.input).is(":checked");e.find(this.input).prop("checked",!c).trigger("change")},n.prototype.radiobtn=function(c,n){var t=e('input:radio[name="'+n+'"]');t.prop("checked",!1),t.closest(t.closest(h)).removeClass("checked"),c.addClass("checked"),c.find(this.input).get(0).checked=c.hasClass("checked"),c.find(this.input).change()},o.on("change",t),s.on("change",t),d.find("a").on("click",function(e){e.stopPropagation()}),d.on("click",function(c){c.preventDefault(),f.checkbox(e(this)),c=e(this).attr("data-toggle"),e(c).toggleClass("is-hidden"),l(e(this))}),h.on("click",function(c){c.preventDefault(),k.radiobtn(e(this),e(this).find("input:radio").attr("name")),l(e(this))}),c.checkAllButton&&c.checkAllTarget){var u=e(this);u.find(e(c.checkAllButton)).on("click",function(){u.find(c.checkAllTarget).find("input:checkbox").each(function(){u.find(e(c.checkAllButton)).hasClass("checked")?u.find(c.checkAllTarget).find("input:checkbox").prop("checked",!0).change():u.find(c.checkAllTarget).find("input:checkbox").prop("checked",!1).change()}),i(u.find(e(c.checkAllButton)).find(".toggle-text"),c.checkAllTextDefault,c.checkAllTextToggle)}),u.find(c.checkAllTarget).find(d).on("click",function(){u.find(c.checkAllButton).find("input:checkbox").prop("checked",!1).change().removeClass("checked"),i(u.find(e(c.checkAllButton)).find(".toggle-text"),c.checkAllTextDefault,c.checkAllTextToggle)})}a.find('[checked="checked"]').closest("label").addClass("checked"),a.find("input").is("input:disabled")&&a.find("input:disabled").closest("label").off().addClass("disabled")})}}(jQuery,window,document);
/* custom checkbox and radio*/

/*time picker */
(function($){$.ui.timepicker=$.ui.timepicker||{};if($.ui.timepicker.version){return}$.extend($.ui,{timepicker:{version:"1.4.3"}});var Timepicker=function(){this.regional=[];this.regional[""]={currentText:"Now",closeText:"Done",amNames:["AM","A"],pmNames:["PM","P"],timeFormat:"HH:mm",timeSuffix:"",timeOnlyTitle:"Choose Time",timeText:"Time",hourText:"Hour",minuteText:"Minute",secondText:"Second",millisecText:"Millisecond",microsecText:"Microsecond",timezoneText:"Time Zone",isRTL:false};this._defaults={showButtonPanel:true,timeOnly:false,showHour:null,showMinute:null,showSecond:null,showMillisec:null,showMicrosec:null,showTimezone:null,showTime:true,stepHour:1,stepMinute:1,stepSecond:1,stepMillisec:1,stepMicrosec:1,hour:0,minute:0,second:0,millisec:0,microsec:0,timezone:null,hourMin:0,minuteMin:0,secondMin:0,millisecMin:0,microsecMin:0,hourMax:23,minuteMax:59,secondMax:59,millisecMax:999,microsecMax:999,minDateTime:null,maxDateTime:null,onSelect:null,hourGrid:0,minuteGrid:0,secondGrid:0,millisecGrid:0,microsecGrid:0,alwaysSetTime:true,separator:" ",altFieldTimeOnly:true,altTimeFormat:null,altSeparator:null,altTimeSuffix:null,pickerTimeFormat:null,pickerTimeSuffix:null,showTimepicker:true,timezoneList:null,addSliderAccess:false,sliderAccessArgs:null,controlType:"slider",defaultValue:null,parse:"strict"};$.extend(this._defaults,this.regional[""])};$.extend(Timepicker.prototype,{$input:null,$altInput:null,$timeObj:null,inst:null,hour_slider:null,minute_slider:null,second_slider:null,millisec_slider:null,microsec_slider:null,timezone_select:null,hour:0,minute:0,second:0,millisec:0,microsec:0,timezone:null,hourMinOriginal:null,minuteMinOriginal:null,secondMinOriginal:null,millisecMinOriginal:null,microsecMinOriginal:null,hourMaxOriginal:null,minuteMaxOriginal:null,secondMaxOriginal:null,millisecMaxOriginal:null,microsecMaxOriginal:null,ampm:"",formattedDate:"",formattedTime:"",formattedDateTime:"",timezoneList:null,units:["hour","minute","second","millisec","microsec"],support:{},control:null,setDefaults:function(e){extendRemove(this._defaults,e||{});return this},_newInst:function($input,opts){var tp_inst=new Timepicker,inlineSettings={},fns={},overrides,i;for(var attrName in this._defaults){if(this._defaults.hasOwnProperty(attrName)){var attrValue=$input.attr("time:"+attrName);if(attrValue){try{inlineSettings[attrName]=eval(attrValue)}catch(err){inlineSettings[attrName]=attrValue}}}}overrides={beforeShow:function(e,t){if($.isFunction(tp_inst._defaults.evnts.beforeShow)){return tp_inst._defaults.evnts.beforeShow.call($input[0],e,t,tp_inst)}},onChangeMonthYear:function(e,t,n){tp_inst._updateDateTime(n);if($.isFunction(tp_inst._defaults.evnts.onChangeMonthYear)){tp_inst._defaults.evnts.onChangeMonthYear.call($input[0],e,t,n,tp_inst)}},onClose:function(e,t){if(tp_inst.timeDefined===true&&$input.val()!==""){tp_inst._updateDateTime(t)}if($.isFunction(tp_inst._defaults.evnts.onClose)){tp_inst._defaults.evnts.onClose.call($input[0],e,t,tp_inst)}}};for(i in overrides){if(overrides.hasOwnProperty(i)){fns[i]=opts[i]||null}}tp_inst._defaults=$.extend({},this._defaults,inlineSettings,opts,overrides,{evnts:fns,timepicker:tp_inst});tp_inst.amNames=$.map(tp_inst._defaults.amNames,function(e){return e.toUpperCase()});tp_inst.pmNames=$.map(tp_inst._defaults.pmNames,function(e){return e.toUpperCase()});tp_inst.support=detectSupport(tp_inst._defaults.timeFormat+(tp_inst._defaults.pickerTimeFormat?tp_inst._defaults.pickerTimeFormat:"")+(tp_inst._defaults.altTimeFormat?tp_inst._defaults.altTimeFormat:""));if(typeof tp_inst._defaults.controlType==="string"){if(tp_inst._defaults.controlType==="slider"&&typeof $.ui.slider==="undefined"){tp_inst._defaults.controlType="select"}tp_inst.control=tp_inst._controls[tp_inst._defaults.controlType]}else{tp_inst.control=tp_inst._defaults.controlType}var timezoneList=[-720,-660,-600,-570,-540,-480,-420,-360,-300,-270,-240,-210,-180,-120,-60,0,60,120,180,210,240,270,300,330,345,360,390,420,480,525,540,570,600,630,660,690,720,765,780,840];if(tp_inst._defaults.timezoneList!==null){timezoneList=tp_inst._defaults.timezoneList}var tzl=timezoneList.length,tzi=0,tzv=null;if(tzl>0&&typeof timezoneList[0]!=="object"){for(;tzi<tzl;tzi++){tzv=timezoneList[tzi];timezoneList[tzi]={value:tzv,label:$.timepicker.timezoneOffsetString(tzv,tp_inst.support.iso8601)}}}tp_inst._defaults.timezoneList=timezoneList;tp_inst.timezone=tp_inst._defaults.timezone!==null?$.timepicker.timezoneOffsetNumber(tp_inst._defaults.timezone):(new Date).getTimezoneOffset()*-1;tp_inst.hour=tp_inst._defaults.hour<tp_inst._defaults.hourMin?tp_inst._defaults.hourMin:tp_inst._defaults.hour>tp_inst._defaults.hourMax?tp_inst._defaults.hourMax:tp_inst._defaults.hour;tp_inst.minute=tp_inst._defaults.minute<tp_inst._defaults.minuteMin?tp_inst._defaults.minuteMin:tp_inst._defaults.minute>tp_inst._defaults.minuteMax?tp_inst._defaults.minuteMax:tp_inst._defaults.minute;tp_inst.second=tp_inst._defaults.second<tp_inst._defaults.secondMin?tp_inst._defaults.secondMin:tp_inst._defaults.second>tp_inst._defaults.secondMax?tp_inst._defaults.secondMax:tp_inst._defaults.second;tp_inst.millisec=tp_inst._defaults.millisec<tp_inst._defaults.millisecMin?tp_inst._defaults.millisecMin:tp_inst._defaults.millisec>tp_inst._defaults.millisecMax?tp_inst._defaults.millisecMax:tp_inst._defaults.millisec;tp_inst.microsec=tp_inst._defaults.microsec<tp_inst._defaults.microsecMin?tp_inst._defaults.microsecMin:tp_inst._defaults.microsec>tp_inst._defaults.microsecMax?tp_inst._defaults.microsecMax:tp_inst._defaults.microsec;tp_inst.ampm="";tp_inst.$input=$input;if(tp_inst._defaults.altField){tp_inst.$altInput=$(tp_inst._defaults.altField).css({cursor:"pointer"}).focus(function(){$input.trigger("focus")})}if(tp_inst._defaults.minDate===0||tp_inst._defaults.minDateTime===0){tp_inst._defaults.minDate=new Date}if(tp_inst._defaults.maxDate===0||tp_inst._defaults.maxDateTime===0){tp_inst._defaults.maxDate=new Date}if(tp_inst._defaults.minDate!==undefined&&tp_inst._defaults.minDate instanceof Date){tp_inst._defaults.minDateTime=new Date(tp_inst._defaults.minDate.getTime())}if(tp_inst._defaults.minDateTime!==undefined&&tp_inst._defaults.minDateTime instanceof Date){tp_inst._defaults.minDate=new Date(tp_inst._defaults.minDateTime.getTime())}if(tp_inst._defaults.maxDate!==undefined&&tp_inst._defaults.maxDate instanceof Date){tp_inst._defaults.maxDateTime=new Date(tp_inst._defaults.maxDate.getTime())}if(tp_inst._defaults.maxDateTime!==undefined&&tp_inst._defaults.maxDateTime instanceof Date){tp_inst._defaults.maxDate=new Date(tp_inst._defaults.maxDateTime.getTime())}tp_inst.$input.bind("focus",function(){tp_inst._onFocus()});return tp_inst},_addTimePicker:function(e){var t=this.$altInput&&this._defaults.altFieldTimeOnly?this.$input.val()+" "+this.$altInput.val():this.$input.val();this.timeDefined=this._parseTime(t);this._limitMinMaxDateTime(e,false);this._injectTimePicker()},_parseTime:function(e,t){if(!this.inst){this.inst=$.datepicker._getInst(this.$input[0])}if(t||!this._defaults.timeOnly){var n=$.datepicker._get(this.inst,"dateFormat");try{var r=parseDateTimeInternal(n,this._defaults.timeFormat,e,$.datepicker._getFormatConfig(this.inst),this._defaults);if(!r.timeObj){return false}$.extend(this,r.timeObj)}catch(i){$.timepicker.log("Error parsing the date/time string: "+i+"\ndate/time string = "+e+"\ntimeFormat = "+this._defaults.timeFormat+"\ndateFormat = "+n);return false}return true}else{var s=$.datepicker.parseTime(this._defaults.timeFormat,e,this._defaults);if(!s){return false}$.extend(this,s);return true}},_injectTimePicker:function(){var e=this.inst.dpDiv,t=this.inst.settings,n=this,r="",i="",s=null,o={},u={},a=null,f=0,l=0;if(e.find("div.ui-timepicker-div").length===0&&t.showTimepicker){var c=' style="display:none;"',h='<div class="ui-timepicker-div'+(t.isRTL?" ui-timepicker-rtl":"")+'"><dl>'+'<dt class="ui_tpicker_time_label"'+(t.showTime?"":c)+">"+t.timeText+"</dt>"+'<dd class="ui_tpicker_time"'+(t.showTime?"":c)+"></dd>";for(f=0,l=this.units.length;f<l;f++){r=this.units[f];i=r.substr(0,1).toUpperCase()+r.substr(1);s=t["show"+i]!==null?t["show"+i]:this.support[r];o[r]=parseInt(t[r+"Max"]-(t[r+"Max"]-t[r+"Min"])%t["step"+i],10);u[r]=0;h+='<dt class="ui_tpicker_'+r+'_label"'+(s?"":c)+">"+t[r+"Text"]+"</dt>"+'<dd class="ui_tpicker_'+r+'"><div class="ui_tpicker_'+r+'_slider"'+(s?"":c)+"></div>";if(s&&t[r+"Grid"]>0){h+='<div style="padding-left: 1px"><table class="ui-tpicker-grid-label"><tr>';if(r==="hour"){for(var p=t[r+"Min"];p<=o[r];p+=parseInt(t[r+"Grid"],10)){u[r]++;var d=$.datepicker.formatTime(this.support.ampm?"hht":"HH",{hour:p},t);h+='<td data-for="'+r+'">'+d+"</td>"}}else{for(var v=t[r+"Min"];v<=o[r];v+=parseInt(t[r+"Grid"],10)){u[r]++;h+='<td data-for="'+r+'">'+(v<10?"0":"")+v+"</td>"}}h+="</tr></table></div>"}h+="</dd>"}var m=t.showTimezone!==null?t.showTimezone:this.support.timezone;h+='<dt class="ui_tpicker_timezone_label"'+(m?"":c)+">"+t.timezoneText+"</dt>";h+='<dd class="ui_tpicker_timezone" '+(m?"":c)+"></dd>";h+="</dl></div>";var g=$(h);if(t.timeOnly===true){g.prepend('<div class="ui-widget-header ui-helper-clearfix ui-corner-all">'+'<div class="ui-datepicker-title">'+t.timeOnlyTitle+"</div>"+"</div>");e.find(".ui-datepicker-header, .ui-datepicker-calendar").hide()}for(f=0,l=n.units.length;f<l;f++){r=n.units[f];i=r.substr(0,1).toUpperCase()+r.substr(1);s=t["show"+i]!==null?t["show"+i]:this.support[r];n[r+"_slider"]=n.control.create(n,g.find(".ui_tpicker_"+r+"_slider"),r,n[r],t[r+"Min"],o[r],t["step"+i]);if(s&&t[r+"Grid"]>0){a=100*u[r]*t[r+"Grid"]/(o[r]-t[r+"Min"]);g.find(".ui_tpicker_"+r+" table").css({width:a+"%",marginLeft:t.isRTL?"0":a/(-2*u[r])+"%",marginRight:t.isRTL?a/(-2*u[r])+"%":"0",borderCollapse:"collapse"}).find("td").click(function(e){var t=$(this),i=t.html(),s=parseInt(i.replace(/[^0-9]/g),10),o=i.replace(/[^apm]/ig),u=t.data("for");if(u==="hour"){if(o.indexOf("p")!==-1&&s<12){s+=12}else{if(o.indexOf("a")!==-1&&s===12){s=0}}}n.control.value(n,n[u+"_slider"],r,s);n._onTimeChange();n._onSelectHandler()}).css({cursor:"pointer",width:100/u[r]+"%",textAlign:"center",overflow:"hidden"})}}this.timezone_select=g.find(".ui_tpicker_timezone").append("<select></select>").find("select");$.fn.append.apply(this.timezone_select,$.map(t.timezoneList,function(e,t){return $("<option />").val(typeof e==="object"?e.value:e).text(typeof e==="object"?e.label:e)}));if(typeof this.timezone!=="undefined"&&this.timezone!==null&&this.timezone!==""){var y=(new Date(this.inst.selectedYear,this.inst.selectedMonth,this.inst.selectedDay,12)).getTimezoneOffset()*-1;if(y===this.timezone){selectLocalTimezone(n)}else{this.timezone_select.val(this.timezone)}}else{if(typeof this.hour!=="undefined"&&this.hour!==null&&this.hour!==""){this.timezone_select.val(t.timezone)}else{selectLocalTimezone(n)}}this.timezone_select.change(function(){n._onTimeChange();n._onSelectHandler()});var b=e.find(".ui-datepicker-buttonpane");if(b.length){b.before(g)}else{e.append(g)}this.$timeObj=g.find(".ui_tpicker_time");if(this.inst!==null){var w=this.timeDefined;this._onTimeChange();this.timeDefined=w}if(this._defaults.addSliderAccess){var E=this._defaults.sliderAccessArgs,S=this._defaults.isRTL;E.isRTL=S;setTimeout(function(){if(g.find(".ui-slider-access").length===0){g.find(".ui-slider:visible").sliderAccess(E);var e=g.find(".ui-slider-access:eq(0)").outerWidth(true);if(e){g.find("table:visible").each(function(){var t=$(this),n=t.outerWidth(),r=t.css(S?"marginRight":"marginLeft").toString().replace("%",""),i=n-e,s=r*i/n+"%",o={width:i,marginRight:0,marginLeft:0};o[S?"marginRight":"marginLeft"]=s;t.css(o)})}}},10)}n._limitMinMaxDateTime(this.inst,true)}},_limitMinMaxDateTime:function(e,t){var n=this._defaults,r=new Date(e.selectedYear,e.selectedMonth,e.selectedDay);if(!this._defaults.showTimepicker){return}if($.datepicker._get(e,"minDateTime")!==null&&$.datepicker._get(e,"minDateTime")!==undefined&&r){var i=$.datepicker._get(e,"minDateTime"),s=new Date(i.getFullYear(),i.getMonth(),i.getDate(),0,0,0,0);if(this.hourMinOriginal===null||this.minuteMinOriginal===null||this.secondMinOriginal===null||this.millisecMinOriginal===null||this.microsecMinOriginal===null){this.hourMinOriginal=n.hourMin;this.minuteMinOriginal=n.minuteMin;this.secondMinOriginal=n.secondMin;this.millisecMinOriginal=n.millisecMin;this.microsecMinOriginal=n.microsecMin}if(e.settings.timeOnly||s.getTime()===r.getTime()){this._defaults.hourMin=i.getHours();if(this.hour<=this._defaults.hourMin){this.hour=this._defaults.hourMin;this._defaults.minuteMin=i.getMinutes();if(this.minute<=this._defaults.minuteMin){this.minute=this._defaults.minuteMin;this._defaults.secondMin=i.getSeconds();if(this.second<=this._defaults.secondMin){this.second=this._defaults.secondMin;this._defaults.millisecMin=i.getMilliseconds();if(this.millisec<=this._defaults.millisecMin){this.millisec=this._defaults.millisecMin;this._defaults.microsecMin=i.getMicroseconds()}else{if(this.microsec<this._defaults.microsecMin){this.microsec=this._defaults.microsecMin}this._defaults.microsecMin=this.microsecMinOriginal}}else{this._defaults.millisecMin=this.millisecMinOriginal;this._defaults.microsecMin=this.microsecMinOriginal}}else{this._defaults.secondMin=this.secondMinOriginal;this._defaults.millisecMin=this.millisecMinOriginal;this._defaults.microsecMin=this.microsecMinOriginal}}else{this._defaults.minuteMin=this.minuteMinOriginal;this._defaults.secondMin=this.secondMinOriginal;this._defaults.millisecMin=this.millisecMinOriginal;this._defaults.microsecMin=this.microsecMinOriginal}}else{this._defaults.hourMin=this.hourMinOriginal;this._defaults.minuteMin=this.minuteMinOriginal;this._defaults.secondMin=this.secondMinOriginal;this._defaults.millisecMin=this.millisecMinOriginal;this._defaults.microsecMin=this.microsecMinOriginal}}if($.datepicker._get(e,"maxDateTime")!==null&&$.datepicker._get(e,"maxDateTime")!==undefined&&r){var o=$.datepicker._get(e,"maxDateTime"),u=new Date(o.getFullYear(),o.getMonth(),o.getDate(),0,0,0,0);if(this.hourMaxOriginal===null||this.minuteMaxOriginal===null||this.secondMaxOriginal===null||this.millisecMaxOriginal===null){this.hourMaxOriginal=n.hourMax;this.minuteMaxOriginal=n.minuteMax;this.secondMaxOriginal=n.secondMax;this.millisecMaxOriginal=n.millisecMax;this.microsecMaxOriginal=n.microsecMax}if(e.settings.timeOnly||u.getTime()===r.getTime()){this._defaults.hourMax=o.getHours();if(this.hour>=this._defaults.hourMax){this.hour=this._defaults.hourMax;this._defaults.minuteMax=o.getMinutes();if(this.minute>=this._defaults.minuteMax){this.minute=this._defaults.minuteMax;this._defaults.secondMax=o.getSeconds();if(this.second>=this._defaults.secondMax){this.second=this._defaults.secondMax;this._defaults.millisecMax=o.getMilliseconds();if(this.millisec>=this._defaults.millisecMax){this.millisec=this._defaults.millisecMax;this._defaults.microsecMax=o.getMicroseconds()}else{if(this.microsec>this._defaults.microsecMax){this.microsec=this._defaults.microsecMax}this._defaults.microsecMax=this.microsecMaxOriginal}}else{this._defaults.millisecMax=this.millisecMaxOriginal;this._defaults.microsecMax=this.microsecMaxOriginal}}else{this._defaults.secondMax=this.secondMaxOriginal;this._defaults.millisecMax=this.millisecMaxOriginal;this._defaults.microsecMax=this.microsecMaxOriginal}}else{this._defaults.minuteMax=this.minuteMaxOriginal;this._defaults.secondMax=this.secondMaxOriginal;this._defaults.millisecMax=this.millisecMaxOriginal;this._defaults.microsecMax=this.microsecMaxOriginal}}else{this._defaults.hourMax=this.hourMaxOriginal;this._defaults.minuteMax=this.minuteMaxOriginal;this._defaults.secondMax=this.secondMaxOriginal;this._defaults.millisecMax=this.millisecMaxOriginal;this._defaults.microsecMax=this.microsecMaxOriginal}}if(t!==undefined&&t===true){var a=parseInt(this._defaults.hourMax-(this._defaults.hourMax-this._defaults.hourMin)%this._defaults.stepHour,10),f=parseInt(this._defaults.minuteMax-(this._defaults.minuteMax-this._defaults.minuteMin)%this._defaults.stepMinute,10),l=parseInt(this._defaults.secondMax-(this._defaults.secondMax-this._defaults.secondMin)%this._defaults.stepSecond,10),c=parseInt(this._defaults.millisecMax-(this._defaults.millisecMax-this._defaults.millisecMin)%this._defaults.stepMillisec,10),h=parseInt(this._defaults.microsecMax-(this._defaults.microsecMax-this._defaults.microsecMin)%this._defaults.stepMicrosec,10);if(this.hour_slider){this.control.options(this,this.hour_slider,"hour",{min:this._defaults.hourMin,max:a});this.control.value(this,this.hour_slider,"hour",this.hour-this.hour%this._defaults.stepHour)}if(this.minute_slider){this.control.options(this,this.minute_slider,"minute",{min:this._defaults.minuteMin,max:f});this.control.value(this,this.minute_slider,"minute",this.minute-this.minute%this._defaults.stepMinute)}if(this.second_slider){this.control.options(this,this.second_slider,"second",{min:this._defaults.secondMin,max:l});this.control.value(this,this.second_slider,"second",this.second-this.second%this._defaults.stepSecond)}if(this.millisec_slider){this.control.options(this,this.millisec_slider,"millisec",{min:this._defaults.millisecMin,max:c});this.control.value(this,this.millisec_slider,"millisec",this.millisec-this.millisec%this._defaults.stepMillisec)}if(this.microsec_slider){this.control.options(this,this.microsec_slider,"microsec",{min:this._defaults.microsecMin,max:h});this.control.value(this,this.microsec_slider,"microsec",this.microsec-this.microsec%this._defaults.stepMicrosec)}}},_onTimeChange:function(){if(!this._defaults.showTimepicker){return}var e=this.hour_slider?this.control.value(this,this.hour_slider,"hour"):false,t=this.minute_slider?this.control.value(this,this.minute_slider,"minute"):false,n=this.second_slider?this.control.value(this,this.second_slider,"second"):false,r=this.millisec_slider?this.control.value(this,this.millisec_slider,"millisec"):false,i=this.microsec_slider?this.control.value(this,this.microsec_slider,"microsec"):false,s=this.timezone_select?this.timezone_select.val():false,o=this._defaults,u=o.pickerTimeFormat||o.timeFormat,a=o.pickerTimeSuffix||o.timeSuffix;if(typeof e==="object"){e=false}if(typeof t==="object"){t=false}if(typeof n==="object"){n=false}if(typeof r==="object"){r=false}if(typeof i==="object"){i=false}if(typeof s==="object"){s=false}if(e!==false){e=parseInt(e,10)}if(t!==false){t=parseInt(t,10)}if(n!==false){n=parseInt(n,10)}if(r!==false){r=parseInt(r,10)}if(i!==false){i=parseInt(i,10)}if(s!==false){s=s.toString()}var f=o[e<12?"amNames":"pmNames"][0];var l=e!==parseInt(this.hour,10)||t!==parseInt(this.minute,10)||n!==parseInt(this.second,10)||r!==parseInt(this.millisec,10)||i!==parseInt(this.microsec,10)||this.ampm.length>0&&e<12!==($.inArray(this.ampm.toUpperCase(),this.amNames)!==-1)||this.timezone!==null&&s!==this.timezone.toString();if(l){if(e!==false){this.hour=e}if(t!==false){this.minute=t}if(n!==false){this.second=n}if(r!==false){this.millisec=r}if(i!==false){this.microsec=i}if(s!==false){this.timezone=s}if(!this.inst){this.inst=$.datepicker._getInst(this.$input[0])}this._limitMinMaxDateTime(this.inst,true)}if(this.support.ampm){this.ampm=f}this.formattedTime=$.datepicker.formatTime(o.timeFormat,this,o);if(this.$timeObj){if(u===o.timeFormat){this.$timeObj.text(this.formattedTime+a)}else{this.$timeObj.text($.datepicker.formatTime(u,this,o)+a)}}this.timeDefined=true;if(l){this._updateDateTime();this.$input.focus()}},_onSelectHandler:function(){var e=this._defaults.onSelect||this.inst.settings.onSelect;var t=this.$input?this.$input[0]:null;if(e&&t){e.apply(t,[this.formattedDateTime,this])}},_updateDateTime:function(e){e=this.inst||e;var t=e.currentYear>0?new Date(e.currentYear,e.currentMonth,e.currentDay):new Date(e.selectedYear,e.selectedMonth,e.selectedDay),n=$.datepicker._daylightSavingAdjust(t),r=$.datepicker._get(e,"dateFormat"),i=$.datepicker._getFormatConfig(e),s=n!==null&&this.timeDefined;this.formattedDate=$.datepicker.formatDate(r,n===null?new Date:n,i);var o=this.formattedDate;if(e.lastVal===""){e.currentYear=e.selectedYear;e.currentMonth=e.selectedMonth;e.currentDay=e.selectedDay}if(this._defaults.timeOnly===true){o=this.formattedTime}else if(this._defaults.timeOnly!==true&&(this._defaults.alwaysSetTime||s)){o+=this._defaults.separator+this.formattedTime+this._defaults.timeSuffix}this.formattedDateTime=o;if(!this._defaults.showTimepicker){this.$input.val(this.formattedDate)}else if(this.$altInput&&this._defaults.timeOnly===false&&this._defaults.altFieldTimeOnly===true){this.$altInput.val(this.formattedTime);this.$input.val(this.formattedDate)}else if(this.$altInput){this.$input.val(o);var u="",a=this._defaults.altSeparator?this._defaults.altSeparator:this._defaults.separator,f=this._defaults.altTimeSuffix?this._defaults.altTimeSuffix:this._defaults.timeSuffix;if(!this._defaults.timeOnly){if(this._defaults.altFormat){u=$.datepicker.formatDate(this._defaults.altFormat,n===null?new Date:n,i)}else{u=this.formattedDate}if(u){u+=a}}if(this._defaults.altTimeFormat){u+=$.datepicker.formatTime(this._defaults.altTimeFormat,this,this._defaults)+f}else{u+=this.formattedTime+f}this.$altInput.val(u)}else{this.$input.val(o)}this.$input.trigger("change")},_onFocus:function(){if(!this.$input.val()&&this._defaults.defaultValue){this.$input.val(this._defaults.defaultValue);var e=$.datepicker._getInst(this.$input.get(0)),t=$.datepicker._get(e,"timepicker");if(t){if(t._defaults.timeOnly&&e.input.val()!==e.lastVal){try{$.datepicker._updateDatepicker(e)}catch(n){$.timepicker.log(n)}}}}},_controls:{slider:{create:function(e,t,n,r,i,s,o){var u=e._defaults.isRTL;return t.prop("slide",null).slider({orientation:"horizontal",value:u?r*-1:r,min:u?s*-1:i,max:u?i*-1:s,step:o,slide:function(t,r){e.control.value(e,$(this),n,u?r.value*-1:r.value);e._onTimeChange()},stop:function(t,n){e._onSelectHandler()}})},options:function(e,t,n,r,i){if(e._defaults.isRTL){if(typeof r==="string"){if(r==="min"||r==="max"){if(i!==undefined){return t.slider(r,i*-1)}return Math.abs(t.slider(r))}return t.slider(r)}var s=r.min,o=r.max;r.min=r.max=null;if(s!==undefined){r.max=s*-1}if(o!==undefined){r.min=o*-1}return t.slider(r)}if(typeof r==="string"&&i!==undefined){return t.slider(r,i)}return t.slider(r)},value:function(e,t,n,r){if(e._defaults.isRTL){if(r!==undefined){return t.slider("value",r*-1)}return Math.abs(t.slider("value"))}if(r!==undefined){return t.slider("value",r)}return t.slider("value")}},select:{create:function(e,t,n,r,i,s,o){var u='<select class="ui-timepicker-select" data-unit="'+n+'" data-min="'+i+'" data-max="'+s+'" data-step="'+o+'">',a=e._defaults.pickerTimeFormat||e._defaults.timeFormat;for(var f=i;f<=s;f+=o){u+='<option value="'+f+'"'+(f===r?" selected":"")+">";if(n==="hour"){u+=$.datepicker.formatTime($.trim(a.replace(/[^ht ]/ig,"")),{hour:f},e._defaults)}else if(n==="millisec"||n==="microsec"||f>=10){u+=f}else{u+="0"+f.toString()}u+="</option>"}u+="</select>";t.children("select").remove();$(u).appendTo(t).change(function(t){e._onTimeChange();e._onSelectHandler()});return t},options:function(e,t,n,r,i){var s={},o=t.children("select");if(typeof r==="string"){if(i===undefined){return o.data(r)}s[r]=i}else{s=r}return e.control.create(e,t,o.data("unit"),o.val(),s.min||o.data("min"),s.max||o.data("max"),s.step||o.data("step"))},value:function(e,t,n,r){var i=t.children("select");if(r!==undefined){return i.val(r)}return i.val()}}}});$.fn.extend({timepicker:function(e){e=e||{};var t=Array.prototype.slice.call(arguments);if(typeof e==="object"){t[0]=$.extend(e,{timeOnly:true})}return $(this).each(function(){$.fn.datetimepicker.apply($(this),t)})},datetimepicker:function(e){e=e||{};var t=arguments;if(typeof e==="string"){if(e==="getDate"){return $.fn.datepicker.apply($(this[0]),t)}else{return this.each(function(){var e=$(this);e.datepicker.apply(e,t)})}}else{return this.each(function(){var t=$(this);t.datepicker($.timepicker._newInst(t,e)._defaults)})}}});$.datepicker.parseDateTime=function(e,t,n,r,i){var s=parseDateTimeInternal(e,t,n,r,i);if(s.timeObj){var o=s.timeObj;s.date.setHours(o.hour,o.minute,o.second,o.millisec);s.date.setMicroseconds(o.microsec)}return s.date};$.datepicker.parseTime=function(e,t,n){var r=extendRemove(extendRemove({},$.timepicker._defaults),n||{}),i=e.replace(/\'.*?\'/g,"").indexOf("Z")!==-1;var s=function(e,t,n){var r=function(e,t){var n=[];if(e){$.merge(n,e)}if(t){$.merge(n,t)}n=$.map(n,function(e){return e.replace(/[.*+?|()\[\]{}\\]/g,"\\$&")});return"("+n.join("|")+")?"};var i=function(e){var t=e.toLowerCase().match(/(h{1,2}|m{1,2}|s{1,2}|l{1}|c{1}|t{1,2}|z|'.*?')/g),n={h:-1,m:-1,s:-1,l:-1,c:-1,t:-1,z:-1};if(t){for(var r=0;r<t.length;r++){if(n[t[r].toString().charAt(0)]===-1){n[t[r].toString().charAt(0)]=r+1}}}return n};var s="^"+e.toString().replace(/([hH]{1,2}|mm?|ss?|[tT]{1,2}|[zZ]|[lc]|'.*?')/g,function(e){var t=e.length;switch(e.charAt(0).toLowerCase()){case"h":return t===1?"(\\d?\\d)":"(\\d{"+t+"})";case"m":return t===1?"(\\d?\\d)":"(\\d{"+t+"})";case"s":return t===1?"(\\d?\\d)":"(\\d{"+t+"})";case"l":return"(\\d?\\d?\\d)";case"c":return"(\\d?\\d?\\d)";case"z":return"(z|[-+]\\d\\d:?\\d\\d|\\S+)?";case"t":return r(n.amNames,n.pmNames);default:return"("+e.replace(/\'/g,"").replace(/(\.|\$|\^|\\|\/|\(|\)|\[|\]|\?|\+|\*)/g,function(e){return"\\"+e})+")?"}}).replace(/\s/g,"\\s?")+n.timeSuffix+"$",o=i(e),u="",a;a=t.match(new RegExp(s,"i"));var f={hour:0,minute:0,second:0,millisec:0,microsec:0};if(a){if(o.t!==-1){if(a[o.t]===undefined||a[o.t].length===0){u="";f.ampm=""}else{u=$.inArray(a[o.t].toUpperCase(),n.amNames)!==-1?"AM":"PM";f.ampm=n[u==="AM"?"amNames":"pmNames"][0]}}if(o.h!==-1){if(u==="AM"&&a[o.h]==="12"){f.hour=0}else{if(u==="PM"&&a[o.h]!=="12"){f.hour=parseInt(a[o.h],10)+12}else{f.hour=Number(a[o.h])}}}if(o.m!==-1){f.minute=Number(a[o.m])}if(o.s!==-1){f.second=Number(a[o.s])}if(o.l!==-1){f.millisec=Number(a[o.l])}if(o.c!==-1){f.microsec=Number(a[o.c])}if(o.z!==-1&&a[o.z]!==undefined){f.timezone=$.timepicker.timezoneOffsetNumber(a[o.z])}return f}return false};var o=function(e,t,n){try{var r=new Date("2012-01-01 "+t);if(isNaN(r.getTime())){r=new Date("2012-01-01T"+t);if(isNaN(r.getTime())){r=new Date("01/01/2012 "+t);if(isNaN(r.getTime())){throw"Unable to parse time with native Date: "+t}}}return{hour:r.getHours(),minute:r.getMinutes(),second:r.getSeconds(),millisec:r.getMilliseconds(),microsec:r.getMicroseconds(),timezone:r.getTimezoneOffset()*-1}}catch(i){try{return s(e,t,n)}catch(o){$.timepicker.log("Unable to parse \ntimeString: "+t+"\ntimeFormat: "+e)}}return false};if(typeof r.parse==="function"){return r.parse(e,t,r)}if(r.parse==="loose"){return o(e,t,r)}return s(e,t,r)};$.datepicker.formatTime=function(e,t,n){n=n||{};n=$.extend({},$.timepicker._defaults,n);t=$.extend({hour:0,minute:0,second:0,millisec:0,microsec:0,timezone:null},t);var r=e,i=n.amNames[0],s=parseInt(t.hour,10);if(s>11){i=n.pmNames[0]}r=r.replace(/(?:HH?|hh?|mm?|ss?|[tT]{1,2}|[zZ]|[lc]|'.*?')/g,function(e){switch(e){case"HH":return("0"+s).slice(-2);case"H":return s;case"hh":return("0"+convert24to12(s)).slice(-2);case"h":return convert24to12(s);case"mm":return("0"+t.minute).slice(-2);case"m":return t.minute;case"ss":return("0"+t.second).slice(-2);case"s":return t.second;case"l":return("00"+t.millisec).slice(-3);case"c":return("00"+t.microsec).slice(-3);case"z":return $.timepicker.timezoneOffsetString(t.timezone===null?n.timezone:t.timezone,false);case"Z":return $.timepicker.timezoneOffsetString(t.timezone===null?n.timezone:t.timezone,true);case"T":return i.charAt(0).toUpperCase();case"TT":return i.toUpperCase();case"t":return i.charAt(0).toLowerCase();case"tt":return i.toLowerCase();default:return e.replace(/'/g,"")}});return r};$.datepicker._base_selectDate=$.datepicker._selectDate;$.datepicker._selectDate=function(e,t){var n=this._getInst($(e)[0]),r=this._get(n,"timepicker");if(r){r._limitMinMaxDateTime(n,true);n.inline=n.stay_open=true;this._base_selectDate(e,t);n.inline=n.stay_open=false;this._notifyChange(n);this._updateDatepicker(n)}else{this._base_selectDate(e,t)}};$.datepicker._base_updateDatepicker=$.datepicker._updateDatepicker;$.datepicker._updateDatepicker=function(e){var t=e.input[0];if($.datepicker._curInst&&$.datepicker._curInst!==e&&$.datepicker._datepickerShowing&&$.datepicker._lastInput!==t){return}if(typeof e.stay_open!=="boolean"||e.stay_open===false){this._base_updateDatepicker(e);var n=this._get(e,"timepicker");if(n){n._addTimePicker(e)}}};$.datepicker._base_doKeyPress=$.datepicker._doKeyPress;$.datepicker._doKeyPress=function(e){var t=$.datepicker._getInst(e.target),n=$.datepicker._get(t,"timepicker");if(n){if($.datepicker._get(t,"constrainInput")){var r=n.support.ampm,i=n._defaults.showTimezone!==null?n._defaults.showTimezone:n.support.timezone,s=$.datepicker._possibleChars($.datepicker._get(t,"dateFormat")),o=n._defaults.timeFormat.toString().replace(/[hms]/g,"").replace(/TT/g,r?"APM":"").replace(/Tt/g,r?"AaPpMm":"").replace(/tT/g,r?"AaPpMm":"").replace(/T/g,r?"AP":"").replace(/tt/g,r?"apm":"").replace(/t/g,r?"ap":"")+" "+n._defaults.separator+n._defaults.timeSuffix+(i?n._defaults.timezoneList.join(""):"")+n._defaults.amNames.join("")+n._defaults.pmNames.join("")+s,u=String.fromCharCode(e.charCode===undefined?e.keyCode:e.charCode);return e.ctrlKey||u<" "||!s||o.indexOf(u)>-1}}return $.datepicker._base_doKeyPress(e)};$.datepicker._base_updateAlternate=$.datepicker._updateAlternate;$.datepicker._updateAlternate=function(e){var t=this._get(e,"timepicker");if(t){var n=t._defaults.altField;if(n){var r=t._defaults.altFormat||t._defaults.dateFormat,i=this._getDate(e),s=$.datepicker._getFormatConfig(e),o="",u=t._defaults.altSeparator?t._defaults.altSeparator:t._defaults.separator,a=t._defaults.altTimeSuffix?t._defaults.altTimeSuffix:t._defaults.timeSuffix,f=t._defaults.altTimeFormat!==null?t._defaults.altTimeFormat:t._defaults.timeFormat;o+=$.datepicker.formatTime(f,t,t._defaults)+a;if(!t._defaults.timeOnly&&!t._defaults.altFieldTimeOnly&&i!==null){if(t._defaults.altFormat){o=$.datepicker.formatDate(t._defaults.altFormat,i,s)+u+o}else{o=t.formattedDate+u+o}}$(n).val(o)}}else{$.datepicker._base_updateAlternate(e)}};$.datepicker._base_doKeyUp=$.datepicker._doKeyUp;$.datepicker._doKeyUp=function(e){var t=$.datepicker._getInst(e.target),n=$.datepicker._get(t,"timepicker");if(n){if(n._defaults.timeOnly&&t.input.val()!==t.lastVal){try{$.datepicker._updateDatepicker(t)}catch(r){$.timepicker.log(r)}}}return $.datepicker._base_doKeyUp(e)};$.datepicker._base_gotoToday=$.datepicker._gotoToday;$.datepicker._gotoToday=function(e){var t=this._getInst($(e)[0]),n=t.dpDiv;this._base_gotoToday(e);var r=this._get(t,"timepicker");selectLocalTimezone(r);var i=new Date;this._setTime(t,i);$(".ui-datepicker-today",n).click()};$.datepicker._disableTimepickerDatepicker=function(e){var t=this._getInst(e);if(!t){return}var n=this._get(t,"timepicker");$(e).datepicker("getDate");if(n){t.settings.showTimepicker=false;n._defaults.showTimepicker=false;n._updateDateTime(t)}};$.datepicker._enableTimepickerDatepicker=function(e){var t=this._getInst(e);if(!t){return}var n=this._get(t,"timepicker");$(e).datepicker("getDate");if(n){t.settings.showTimepicker=true;n._defaults.showTimepicker=true;n._addTimePicker(t);n._updateDateTime(t)}};$.datepicker._setTime=function(e,t){var n=this._get(e,"timepicker");if(n){var r=n._defaults;n.hour=t?t.getHours():r.hour;n.minute=t?t.getMinutes():r.minute;n.second=t?t.getSeconds():r.second;n.millisec=t?t.getMilliseconds():r.millisec;n.microsec=t?t.getMicroseconds():r.microsec;n._limitMinMaxDateTime(e,true);n._onTimeChange();n._updateDateTime(e)}};$.datepicker._setTimeDatepicker=function(e,t,n){var r=this._getInst(e);if(!r){return}var i=this._get(r,"timepicker");if(i){this._setDateFromField(r);var s;if(t){if(typeof t==="string"){i._parseTime(t,n);s=new Date;s.setHours(i.hour,i.minute,i.second,i.millisec);s.setMicroseconds(i.microsec)}else{s=new Date(t.getTime());s.setMicroseconds(t.getMicroseconds())}if(s.toString()==="Invalid Date"){s=undefined}this._setTime(r,s)}}};$.datepicker._base_setDateDatepicker=$.datepicker._setDateDatepicker;$.datepicker._setDateDatepicker=function(e,t){var n=this._getInst(e);if(!n){return}if(typeof t==="string"){t=new Date(t);if(!t.getTime()){$.timepicker.log("Error creating Date object from string.")}}var r=this._get(n,"timepicker");var i;if(t instanceof Date){i=new Date(t.getTime());i.setMicroseconds(t.getMicroseconds())}else{i=t}if(r&&i){if(!r.support.timezone&&r._defaults.timezone===null){r.timezone=i.getTimezoneOffset()*-1}t=$.timepicker.timezoneAdjust(t,r.timezone);i=$.timepicker.timezoneAdjust(i,r.timezone)}this._updateDatepicker(n);this._base_setDateDatepicker.apply(this,arguments);this._setTimeDatepicker(e,i,true)};$.datepicker._base_getDateDatepicker=$.datepicker._getDateDatepicker;$.datepicker._getDateDatepicker=function(e,t){var n=this._getInst(e);if(!n){return}var r=this._get(n,"timepicker");if(r){if(n.lastVal===undefined){this._setDateFromField(n,t)}var i=this._getDate(n);if(i&&r._parseTime($(e).val(),r.timeOnly)){i.setHours(r.hour,r.minute,r.second,r.millisec);i.setMicroseconds(r.microsec);if(r.timezone!=null){if(!r.support.timezone&&r._defaults.timezone===null){r.timezone=i.getTimezoneOffset()*-1}i=$.timepicker.timezoneAdjust(i,r.timezone)}}return i}return this._base_getDateDatepicker(e,t)};$.datepicker._base_parseDate=$.datepicker.parseDate;$.datepicker.parseDate=function(e,t,n){var r;try{r=this._base_parseDate(e,t,n)}catch(i){if(i.indexOf(":")>=0){r=this._base_parseDate(e,t.substring(0,t.length-(i.length-i.indexOf(":")-2)),n);$.timepicker.log("Error parsing the date string: "+i+"\ndate string = "+t+"\ndate format = "+e)}else{throw i}}return r};$.datepicker._base_formatDate=$.datepicker._formatDate;$.datepicker._formatDate=function(e,t,n,r){var i=this._get(e,"timepicker");if(i){i._updateDateTime(e);return i.$input.val()}return this._base_formatDate(e)};$.datepicker._base_optionDatepicker=$.datepicker._optionDatepicker;$.datepicker._optionDatepicker=function(e,t,n){var r=this._getInst(e),i;if(!r){return null}var s=this._get(r,"timepicker");if(s){var o=null,u=null,a=null,f=s._defaults.evnts,l={},c;if(typeof t==="string"){if(t==="minDate"||t==="minDateTime"){o=n}else if(t==="maxDate"||t==="maxDateTime"){u=n}else if(t==="onSelect"){a=n}else if(f.hasOwnProperty(t)){if(typeof n==="undefined"){return f[t]}l[t]=n;i={}}}else if(typeof t==="object"){if(t.minDate){o=t.minDate}else if(t.minDateTime){o=t.minDateTime}else if(t.maxDate){u=t.maxDate}else if(t.maxDateTime){u=t.maxDateTime}for(c in f){if(f.hasOwnProperty(c)&&t[c]){l[c]=t[c]}}}for(c in l){if(l.hasOwnProperty(c)){f[c]=l[c];if(!i){i=$.extend({},t)}delete i[c]}}if(i&&isEmptyObject(i)){return}if(o){if(o===0){o=new Date}else{o=new Date(o)}s._defaults.minDate=o;s._defaults.minDateTime=o}else if(u){if(u===0){u=new Date}else{u=new Date(u)}s._defaults.maxDate=u;s._defaults.maxDateTime=u}else if(a){s._defaults.onSelect=a}}if(n===undefined){return this._base_optionDatepicker.call($.datepicker,e,t)}return this._base_optionDatepicker.call($.datepicker,e,i||t,n)};var isEmptyObject=function(e){var t;for(t in e){if(e.hasOwnProperty(t)){return false}}return true};var extendRemove=function(e,t){$.extend(e,t);for(var n in t){if(t[n]===null||t[n]===undefined){e[n]=t[n]}}return e};var detectSupport=function(e){var t=e.replace(/'.*?'/g,"").toLowerCase(),n=function(e,t){return e.indexOf(t)!==-1?true:false};return{hour:n(t,"h"),minute:n(t,"m"),second:n(t,"s"),millisec:n(t,"l"),microsec:n(t,"c"),timezone:n(t,"z"),ampm:n(t,"t")&&n(e,"h"),iso8601:n(e,"Z")}};var convert24to12=function(e){e%=12;if(e===0){e=12}return String(e)};var computeEffectiveSetting=function(e,t){return e&&e[t]?e[t]:$.timepicker._defaults[t]};var splitDateTime=function(e,t){var n=computeEffectiveSetting(t,"separator"),r=computeEffectiveSetting(t,"timeFormat"),i=r.split(n),s=i.length,o=e.split(n),u=o.length;if(u>1){return{dateString:o.splice(0,u-s).join(n),timeString:o.splice(0,s).join(n)}}return{dateString:e,timeString:""}};var parseDateTimeInternal=function(e,t,n,r,i){var s,o,u;o=splitDateTime(n,i);s=$.datepicker._base_parseDate(e,o.dateString,r);if(o.timeString===""){return{date:s}}u=$.datepicker.parseTime(t,o.timeString,i);if(!u){throw"Wrong time format"}return{date:s,timeObj:u}};var selectLocalTimezone=function(e,t){if(e&&e.timezone_select){var n=t||new Date;e.timezone_select.val(-n.getTimezoneOffset())}};$.timepicker=new Timepicker;$.timepicker.timezoneOffsetString=function(e,t){if(isNaN(e)||e>840||e<-720){return e}var n=e,r=n%60,i=(n-r)/60,s=t?":":"",o=(n>=0?"+":"-")+("0"+Math.abs(i)).slice(-2)+s+("0"+Math.abs(r)).slice(-2);if(o==="+00:00"){return"Z"}return o};$.timepicker.timezoneOffsetNumber=function(e){var t=e.toString().replace(":","");if(t.toUpperCase()==="Z"){return 0}if(!/^(\-|\+)\d{4}$/.test(t)){return e}return(t.substr(0,1)==="-"?-1:1)*(parseInt(t.substr(1,2),10)*60+parseInt(t.substr(3,2),10))};$.timepicker.timezoneAdjust=function(e,t){var n=$.timepicker.timezoneOffsetNumber(t);if(!isNaN(n)){e.setMinutes(e.getMinutes()+ -e.getTimezoneOffset()-n)}return e};$.timepicker.timeRange=function(e,t,n){return $.timepicker.handleRange("timepicker",e,t,n)};$.timepicker.datetimeRange=function(e,t,n){$.timepicker.handleRange("datetimepicker",e,t,n)};$.timepicker.dateRange=function(e,t,n){$.timepicker.handleRange("datepicker",e,t,n)};$.timepicker.handleRange=function(e,t,n,r){function i(i,s){var o=t[e]("getDate"),u=n[e]("getDate"),a=i[e]("getDate");if(o!==null){var f=new Date(o.getTime()),l=new Date(o.getTime());f.setMilliseconds(f.getMilliseconds()+r.minInterval);l.setMilliseconds(l.getMilliseconds()+r.maxInterval);if(r.minInterval>0&&f>u){n[e]("setDate",f)}else if(r.maxInterval>0&&l<u){n[e]("setDate",l)}else if(o>u){s[e]("setDate",a)}}}function s(t,n,i){if(!t.val()){return}var s=t[e].call(t,"getDate");if(s!==null&&r.minInterval>0){if(i==="minDate"){s.setMilliseconds(s.getMilliseconds()+r.minInterval)}if(i==="maxDate"){s.setMilliseconds(s.getMilliseconds()-r.minInterval)}}if(s.getTime){n[e].call(n,"option",i,s)}}r=$.extend({},{minInterval:0,maxInterval:0,start:{},end:{}},r);$.fn[e].call(t,$.extend({onClose:function(e,t){i($(this),n)},onSelect:function(e){s($(this),n,"minDate")}},r,r.start));$.fn[e].call(n,$.extend({onClose:function(e,n){i($(this),t)},onSelect:function(e){s($(this),t,"maxDate")}},r,r.end));i(t,n);s(t,n,"minDate");s(n,t,"maxDate");return $([t.get(0),n.get(0)])};$.timepicker.log=function(e){if(window.console){window.console.log(e)}};$.timepicker._util={_extendRemove:extendRemove,_isEmptyObject:isEmptyObject,_convert24to12:convert24to12,_detectSupport:detectSupport,_selectLocalTimezone:selectLocalTimezone,_computeEffectiveSetting:computeEffectiveSetting,_splitDateTime:splitDateTime,_parseDateTimeInternal:parseDateTimeInternal};if(!Date.prototype.getMicroseconds){Date.prototype.microseconds=0;Date.prototype.getMicroseconds=function(){return this.microseconds};Date.prototype.setMicroseconds=function(e){this.setMilliseconds(this.getMilliseconds()+Math.floor(e/1e3));this.microseconds=e%1e3;return this}}$.timepicker.version="1.4.3"})(jQuery)
/*time picker */


function celery($url,celery){
	celery = celery || undefined;
	workstatus = undefined;
	$.ajax({
        type : "GET",
        url: $url,
        dataType : 'json',
        data: {'makequery':celery},
        async:false,
        success:function(result){
			workstatus = result.workstatus
            console.log(result.workstatus)
            if (result.workstatus == 'done'){
				clearInterval(job);
				$body.removeClass("loading");
				//window.open(result.filepath, "_blank")
				window.location.href = result.filepath
            }
        },
        error:function(){
            alert('Task Abort,Retry Again')
        },
    });
    return workstatus
}
