```{javascript}
	var cf_path      = "../../..";

	$(function(){

		g_write_pages = '10';
		g_cur_page = '1';
		g_total_page = '4';
		g_count = '20';
		g_url = "javascript:paging('2026-09-15','2026-09-16',", add="";
		g_sort_code = "0";

		// 국가선택, 중요도선택 시 확인 버튼 클릭이 아닌 종료 시에 체크박스 상태를 처음 상태를 돌리기 위해 저장하고 있기 위함
		g_str_natcd = "cn|us|kr|gb";
		g_str_importance = "3|2|1";
		// 달력선택 시 확인 버튼 클릭이 아닌 종료 시에 날짜를 처음 상태를 돌리기 위해 저장하고 있기 위함
		g_start_date = "2026-09-15";
		g_end_date = "2026-09-16"

		$(document).on("click","li[name=tab_button]",function(){
			
			for( var i = 0; i < $("li[name=tab_button]").length; i++ ) {
				$("li[name=tab_button]")[i].title = "";
			}

			$('.tab_mn li').removeClass("active");			
			$(this)['0'].className = "active";
			$(this)[0].title = "선택됨";
		});	
		

		$(".inform input").click(function(){

			openCal();
			$("#calLayer").show();

		} );

		$( '.inform input' ).keydown(function(key) {

			if (key.keyCode == 13) {
				openCal();
				$("#calLayer").show();
			}
		});
		
		/* 달력 레이어에서 확인 클릭 시*/
		$( '#btn_calClose' ).click( function(){
			var start_date	= $("#datepicker1").val();
			var end_date	= $("#datepicker2").val();
			var arr = getCheckBox();
			
			var str_nation = arr['0'];
			var str_natcd = arr['1'];
			var str_importance = arr['2'];
			
			g_start_date = start_date;
			g_end_date = end_date;

			$.getJSON(cf_path + "/eco/includes/wei/module/json_getData.php", { start_date : start_date, end_date : end_date, str_nation : str_nation, str_natcd : str_natcd, str_importance : str_importance }, function( data ){

				g_cur_page = 1;
				g_url = "javascript:paging('"+start_date+"','"+end_date+"',", add="";
				drawData( g_write_pages, g_count, g_cur_page, g_url, data );

			});

			$( '#calLayer' ).hide();
		
		} );
		
		/* 적용버튼 */
		$( '.btn_apply ' ).click( function(){
			var year  = $("#year option:selected").val();
			var month = $("#month option:selected").val();
			var year2  = $("#year2 option:selected").val();
			var month2 = $("#month2 option:selected").val();
			var index = $('#hidden_idx').val();
			
			chartLoad( "chart_area", index, $( "input[name=estimate]" ).is(":checked" ), year+month, year2+month2 );				
		});

		/* 테이블 팝업 : 국가, 중요도*/
		$( '.open_bodPop' ).click( function(){			

			var popId = $( this ).attr('name');
			var arr = getCheckBox();

			var str_natcd = arr['1'];
			var str_importance = arr['2'];
			
			
			setCheckBox( g_str_natcd, g_str_importance );
			$( '.bod_popup' ).each( function(){

				if( $( this ).attr('id') == popId ){

					$( this ).toggle();
					//$('.bodLayer_mask' ).toggle();
				}
			
			} );
		
		} );

		/* 팝업 : 그래프 */		
		$( document ).on("click", '.open_pop', function(){
			var popId = $( this ).attr('name');

			var idx = $( "button[name="+popId+"]" ).index(this);
			var val = $( "button[name="+popId+"]" ).eq(idx).val();
			var val_arr = val.split(":");

			var index = val_arr['0'];
			var forecast = val_arr['1'];
			var title = val_arr['2'];
			
			// 예상치포함 및 비활성화			
			if( forecast == "" || typeof forecast == "undefined" ) 
				document.getElementById("estimate").disabled = true;
			else 
				document.getElementById("estimate").disabled = false;

			$( '.popup' ).each( function(){
					
				if( $( this ).attr('id') == popId ){
					$('.allLayer_mask' ).toggle();
					$( this ).show();
					$('#hidden_idx').val(index);
					$( "input[name=estimate]" ).attr('checked',false);

					var year  = $("#year option:selected").val();
					var month = $("#month option:selected").val();

					var year2  = $("#year2 option:selected").val();
					var month2 = $("#month2 option:selected").val();
					
					$(".title:eq(0)")['0'].innerHTML = title;
					chartLoad( "chart_area", index, false );
				}
			
			} );			
		});
		
		$( '.btn_popClose' ).click( function(){
			
			$( '.popup, .bod_popup, .bodLayer_mask' ).hide();

			if( $(this).closest('div').prop('class') != "tlt_pop" ) {
				// checkbox 유무
				var arr = getCheckBox();
				
				var str_nation = arr['0'];
				var str_natcd = arr['1'];
				var str_importance = arr['2'];
				var start_date = $( "#datepicker1" ).val();
				var end_date = $( "#datepicker2" ).val();
				//alert( str_nation + " & " + str_natcd );
				// 초기화
				$("#year option:eq(0)").prop("selected",true);
				$("#month option:eq(0)").prop("selected",true);

				$("#year2 option:eq(-1)").prop("selected",true);
				$("#month2 option:eq(-1)").prop("selected",true);

				// layer open 처음에 check 된 값들
				g_str_natcd = str_natcd;
				g_str_importance = str_importance;

				// 국가 및 중요도 선택
				selectData( start_date, end_date, str_nation, str_natcd, str_importance );
			}
		} );
	
		/* 마우스를 눌렀다 놓으면, 레이어 영역 이외 클릭 시 레이어 종류 */
		$( document ).mouseup( function(e){
			// 중요도 레이어 숨기기
			var container_immport = $("#layerImport");
			if( container_immport.has(e.target).length === 0 ) {
				container_immport.hide();
			}
			// 국가선택레이어 숨기기
			var container_nation = $("#layerNation");

			if( container_nation.has(e.target).length === 0 ) {				
				container_nation.hide();				
			}

			// 달력레이어 숨기기
			var container_calendar = $("#calLayer");
			if( container_calendar.has(e.target).length === 0 ) {
				setCalendar( g_start_date, g_end_date );
				container_calendar.hide();
			}
			// 차트레이어 숨기기
			var container_chart = $("#graphLayer");
			if( container_chart.has(e.target).length === 0 ) {
				container_chart.hide();
				// 레이어 마스크 숨기기
				$( '.allLayer_mask' ).hide();
			}
		});

		/* 국가 전체체크 */
		$( '#chk_all' ).change(function () {			
			$( '.nation_list input:checkbox' ).prop('checked', $(this).prop("checked") );
		} );
		
		/* 중요도 전체체크 */
		$( '#chk_imAll' ).change(function () {
			$( '.import_list input:checkbox' ).prop('checked', $(this).prop("checked") );
		} );
		
		/* 중요도 부분체크*/
		$( document ).on( "click","input[name=cb_importance]", function(){

			var state = true;
			$("input[name=cb_importance]").each( function(){
				// 전체 선택 해제인경우
				if( !this.checked ) {
					state = false;
					$("input[id=chk_imAll]").prop("checked",state);
				}
			})
			
			if( state ) {
				// 전체 선택인경우
				$("input[id=chk_imAll]").prop("checked",state);
			}
		
		});
	
		$(document).on("click", "#btn_print", function(){
			//console.log( $(".tab_cnts")[0].innerHTML );
			reportPrint( $(".tab_cnts")[0].innerHTML )
		});

	});
	
	function reportPrint(param){
		
		var host_name = window.location.hostname;
		const setting = "width=890, height=841";
		const objWin = window.open('', 'print', setting);
		objWin.document.open();
		objWin.document.write('<html><head><title>분석 레포트 </title>');
			
		objWin.document.write('<link rel="stylesheet" type="text/css" href="http://'+host_name+'/eco/mp/wei/css/common.css?aa=1616134746">');
		objWin.document.write('<link rel="stylesheet" type="text/css" href="http://'+host_name+'/eco/mp/wei/css/style.css?aa=1616134746">');
		objWin.document.write('<link rel="stylesheet" type="text/css" href="http://'+host_name+'/eco/mp/wei/css/custom.css?aa=1616134746">');
		objWin.document.write('</head><body>');
		objWin.document.write(param);
		objWin.document.write('</body></html>');
		
//		console.log(objWin.document);
		//objWin.focus(); 
		objWin.document.close();

		setTimeout(function() {
			objWin.print();
			objWin.close();
		}, 200);	 


		
	}


	/* datepicker */
	function openCal(){

		$("#sDateCal").datepicker({	
			altField : "#datepicker1",
			dateFormat:"yy-mm-dd",
			monthNames: ['01월', '02월', '03월', '04월', '05월', '06월', '07월', '08월', '09월', '10월', '11월', '12월'],
			dayNamesMin: ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
			showMonthAfterYear:true,
			onSelect: function (dateText, inst) {  
				$("#eDateCal").datepicker( "option", "minDate", $("#sDateCal").val() );
			}
		});

		$("#eDateCal").datepicker({	
			altField : "#datepicker2",
			dateFormat:"yy-mm-dd",
			monthNames: ['01월', '02월', '03월', '04월', '05월', '06월', '07월', '08월', '09월', '10월', '11월', '12월'],
			dayNamesMin: ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
			showMonthAfterYear:true,
			defaultDate: 1,
			onSelect: function (dateText, inst) {  
				$("#sDateCal").datepicker( "option", "maxDate", dateText );
			}
		});
	}
	
	/* 기간 변경 당일, 이번주, 이번달 */
	function periodChange( periodCode ) {

		var start_date = "";
		var end_date = "";
		
		var today = new Date();
		var yy = today.getFullYear();
		var mm = today.getMonth()+1;
		var dd = today.getDate();
		var url = "";

		var arr = getCheckBox();

		var str_nation = arr['0'];
		var str_natcd = arr['1'];
		var str_importance = arr['2'];

		// 이번주
		if( periodCode == 1 ) {
			// 월 : 1, 2, 3, 4, 5,    6, 7
			// 월 ~ 금
			var day = today.getDay();
			// 월요일인 경우
			if( day == "1" ) {
				start_date = yy + "" + attachZero(mm) + "" + attachZero(dd);
				end_date = strToDate( today.setDate( today.getDate() + 5 ) );				
			} else {
			// 월요일이 아닌 경우
				// gap_mon : 월요일까지 갭
				gap_mon = day - 1;
				start_date = strToDate( today.setDate( today.getDate() - gap_mon ) );

				gap_fri = 5 - day;
				// 오늘날짜가 금요일인 경우
				if( gap_fri == 0 ) {
					end_date = strToDate( today.setDate( today.getDate() + gap_mon ) );					
				} else {
				// 금요일이 아닌 경우
					end_date = strToDate( today.setDate( today.getDate() + gap_fri + gap_mon ) );
				}
				
			}
		// 이번달
		} else if( periodCode == 2 ) {

			start_date = strToDate( today.setDate(1) );
			today.setMonth( today.getMonth()+1 );			
			end_date = strToDate( today.setDate(0) );
		// 당일			
		} else {
			trans_mm = attachZero( mm );
			trans_dd = attachZero( dd );
			start_date = yy+""+trans_mm+""+trans_dd;

			end_date = today.setDate( dd + 1 );
			end_date = strToDate( end_date );
			
		}

		start_date = start_date.substring( 0,4 )+ "-" + start_date.substring( 4,6 ) + "-" + start_date.substring( 6,8 );
		end_date   = end_date.substring( 0,4 )+ "-" + end_date.substring( 4,6 ) + "-" + end_date.substring( 6,8 );
		
		g_start_date = start_date;
		g_end_date = end_date;
		g_url = "javascript:paging('"+start_date+"','"+end_date+"',", add="";
		sort_code = "1";
		
		$('#button_sort').attr( "onclick", "javascript:sort('"+sort_code+"','"+start_date+"','"+end_date+"')" );
		$('#datepicker1').val( start_date );
		$('#datepicker2').val( end_date );
		
		$.getJSON(cf_path + "/eco/includes/wei/module/json_getData.php", { start_date : start_date, end_date : end_date, str_nation : str_nation, str_natcd : str_natcd, str_importance : str_importance }, function( data ){

			g_cur_page = 1;
			drawData( g_write_pages, g_count, g_cur_page, g_url, data );

		});
	}
	/* 날짜, 시간, 국가, 경제지표, 실제, 예상, 이전, 중요도, 그래도 데이터 그리기 */
	function drawData( write_pages, count, cur_page, url, data ) {
		
		if( data ) {
			g_cur_page = cur_page;

			start_idx = (cur_page-1)* g_count;
			end_idx = ( parseInt( start_idx ) + parseInt( g_count ) );		
			total_page = ( data['date'].length % count ) == 0 ? parseInt( data['date'].length / count ) : parseInt( data['date'].length / count ) + 1;
			
			if( data['date'].length < end_idx ) {
				end_idx = data['date'].length;
			}

			html = "";
			for( i = start_idx; i < end_idx; i++ ) {
				html += "<tr>";
				html += "<th scope='row'>"+data['date'][i]+"<br>"+data['day'][i]+"</th>";
				html += "<td>"+data['time'][i]+"</td>";
				html += "<td><span class='ico_flag ico_"+data['natcd'][i]+"'></span></td>";
				html += "<td class='tal_l'>"+data['nat_hname'][i]+"</td>";
				html += "<td class='tal_l'>"+data['kevent'][i]+"</td>";
				html += "<td>"+data['actual'][i]+"</td>";
				html += "<td>"+data['forecast'][i]+"</td>";
				html += "<td>"+data['previous'][i]+"</td>";
				html += "<td><span class='"+data['importance_class'][i]+"'>"+data['importance'][i]+"<span></td>";
				html += "<td>";
				if( data['actual'][i] != "" || data['forecast'][i] != "" || data['previous'][i] != "" ) {
					html += "<button type='button' name='graphLayer' class='btn_popChart open_pop' value='"+data['index'][i]+":"+data['forecast'][i]+":"+data['kevent'][i]+"'>차트보기</button>";
				}
				html += "</td>";			
				html += "</tr>";
			}
		} else {
			html = "";
			total_page = 0;
		}

		$('.paging')['0'].innerHTML = get_paging_ajax( parseInt(write_pages), parseInt(cur_page), parseInt(total_page), url, add='');
		$('#tbody_data').empty();
		$('#tbody_data').append(html);	
	}

	/* 날짜에 0 붙이기 */
	function attachZero( val ){
		
		var returnVal = val;

		if( String(val).length == "1" )
			returnVal = "0"+val;
		
		return returnVal;
	}
	
	/* timestamp를 date 날짜로 변경 */
	function strToDate( str ) {
		var val = new Date(str);

		return 	val.getFullYear() + "" + attachZero( val.getMonth()+1 )+ "" + attachZero( val.getDate() );
	}

	function excel() {

		var start_date	= $("#datepicker1").val();
		var end_date	= $("#datepicker2").val();
		var arr = getCheckBox();
		var str_nation = arr['0'];
		var str_natcd = arr['1'];
		var str_importance = arr['2'];
		
		//var p = window.open("./0601_excel.php?start_date="+start_date+"&end_date="+end_date+"&sort_code="+g_sort_code+"&str_nation="+str_nation+"&str_natcd="+str_natcd+"&str_importance="+str_importance, "PrintWins", "_self"); 
		location.href = "./0601_excel.php?start_date="+start_date+"&end_date="+end_date+"&sort_code="+g_sort_code+"&str_nation="+str_nation+"&str_natcd="+str_natcd+"&str_importance="+str_importance;

	}
	
	/* 페이지 데이터 뽑기*/
	function paging( start_date, end_date, cur){
		
		//start_date = start_date.replace(/-/gi,"");
		//end_date = end_date.replace(/-/gi,"");
		
		var arr = getCheckBox();
		var str_nation = arr['0'];
		var str_natcd = arr['1'];
		var str_importance = arr['2'];
		
		$.getJSON(cf_path + "/eco/includes/wei/module/json_getData.php", { start_date : start_date, end_date : end_date, sort_code : g_sort_code, str_nation : str_nation , str_natcd : str_natcd, str_importance : str_importance }, function( data ){
			
			pagingLoadProcess( start_date, end_date, cur, data);
		});
	}
	
	/* 페이지 데이터 그리기*/
	function pagingLoadProcess( start_date, end_date, cur, data ){
		drawData( g_write_pages, g_count, cur, g_url, data );
	}

	/* 날짜 정렬*/
	function sort( sort_code, start_date, end_date ) {
		var arr = getCheckBox();
		var str_nation = arr['0'];
		var str_natcd = arr['1'];
		var str_importance = arr['2'];

		$.getJSON(cf_path + "/eco/includes/wei/module/json_getData.php", { start_date : start_date, end_date : end_date, sort_code : sort_code, str_nation : str_nation, str_natcd : str_natcd, str_importance : str_importance }, function( data ){
			
			if( sort_code == "1" ) {
				g_sort_code = sort_code;
				sort_code = "0";
			} else {
				g_sort_code = sort_code;
				sort_code = "1";
			}
			
			$('#button_sort').attr( "onclick", "javascript:sort('"+sort_code+"','"+start_date+"','"+end_date+"')" );
			drawData( g_write_pages, g_count, g_cur_page, g_url, data );
		});
	}
	
	/* 날짜 값 설정*/
	function setCalendar( start_date, end_date ) {

		$('#datepicker1').val( start_date );
		$('#datepicker2').val( end_date );

	}

	/* 체크박스 값 얻기*/
	function getCheckBox() {
		
		var str_nation = "";
		var str_natcd = "";
		var str_importance = "";
		var arr_str = [];

		$("input[name=cb_nation]").each( function(){
			if(this.checked) {
				str_nation += this.value+"|"; 
				str_natcd  += this.id+"|";
			}
		});

		$("input[name=cb_importance]").each( function(){
			if( this.checked ) {
				if( this.value != "all" )
					str_importance += this.value+"|";
			}
		});
		
		arr_str['0'] = str_nation;
		arr_str['1'] = str_natcd;
		arr_str['2'] = str_importance;

		return arr_str;
	}
	
	/* 국가, 중요도 레이어에서 확인 버튼을 클릭 하지 않은 경우 기존 체크 상태를 유지해주기 위한 함수*/
	function setCheckBox( str_natcd, str_importance ) {

		// 배열화
		var arr_natcd = str_natcd.split("|");
		var arr_importance = str_importance.split("|");

		// 배열 빈문자 체크
		arr_natcd	= isArrEmpty( arr_natcd );
		arr_importance = isArrEmpty( arr_importance );
		
		// 초기화
		$("input[name=cb_nation]").prop( "checked", false );
		$("input[name=cb_importance]").prop( "checked", false );

		
		// 국가선택 체크
		$("input[name=cb_nation]").each( function() {
		// 해당 아이디 값이 배열에 있는지 유무체크
			if( $.inArray( this.id, arr_natcd) != -1 ) {
				this.checked = true;
			}

		});

		// 중요도 체크
		$("input[name=cb_importance]").each( function() {
		// 해당 값이 배열에 있는지 유무체크			
			if( $.inArray( this.value, arr_importance) != -1 ) {				
				this.checked = true;
			}
		});
		
		// 국가 전체선택 체크 
		if( arr_natcd.length == $("input[name=cb_nation]").length ) {			
			$("input[id=chk_all]").prop( "checked", true );
		} else {
			$("input[id=chk_all]").prop( "checked", false );
		}

		// 중요도 전체선택 체크
		if( arr_importance.length == $("input[name=cb_importance]").length ) {			
			$("input[id=chk_imAll]").prop( "checked", true );
		} else {
			$("input[id=chk_imAll]").prop( "checked", false );
		}
	}
	
	/* 배열 빈문자 유무체크 후 빈문자 인덱스 제거 */
	function isArrEmpty( arr ) {
		var idx = 0;

		if( ( idx = $.inArray( "", arr ) ) != -1 ) {
			arr.splice(idx,1);
		}

		return arr;
	}
	
	/* 국가, 달력 데이터 선택 */
	function selectData( start_date, end_date, str_nation, str_natcd, str_importance ) {

		$.getJSON(cf_path + "/eco/includes/wei/module/json_getData.php", { start_date : start_date, end_date : end_date, str_nation : str_nation, str_natcd : str_natcd, str_importance : str_importance }, function( data ){
			g_cur_page = "1";
			drawData( g_write_pages, g_count, g_cur_page, g_url, data );
		});
	}
	
	/* 해당 데이터의 단위 파악*/
	function checkUnit( actual , previous, forecast) {
		
		var return_unit = "";

		return_unit = previous.replace(/[0-9.]/g,"");

		return return_unit;
	}

	function formatBytes(a,b) {

		if( 0 == a ) 
			return "0";

		var c = 1000, d = b || 2, e = ["","K","M","G","T","P","E","Z","Y"], f = Math.floor(Math.log(a)/Math.log(c));return parseFloat((a/Math.pow(c,f)).toFixed(d))+" "+e[f]
		
	}

	/* 차트 업데이트 */
	function chartLoad(div_id, index, state, start_date, end_date ) {

		// 예상치 데이터 기본값 x
		if( typeof state == "undefined" || typeof state == null ) {
			state = false;
		}


		$.getJSON(cf_path + "/eco/includes/wei/module/json_getChart.php", { index : index, start_date : start_date, end_date : end_date }, function (data) {

			// 해당 날짜에 데이터가 없으면 리턴해준다.
			if( data == null ) {
				alert("차트 표본데이터가 부족합니다.");
				return;
			}

			var dataLength = data.length;
			var arr_actual = [];
			var arr_forecast = [];
			
			// 단위체크
			var unit = checkUnit( actual, data['0']['previous'], forecast );

			for( i = 0; i < dataLength; i++ ) {
				
				// 시간 데이터
				var dt_y = parseInt( ( data[i]['date'] ).substring(0,4) );
				var dt_m = parseInt( ( data[i]['date'] ).substring(5,7) -1);
				var dt_d = parseInt( ( data[i]['date'] ).substring(8,10) );
				var dt_h = parseInt( ( data[i]['date'] ).substring(11,13));
				var dt_i = parseInt( ( data[i]['date'] ).substring(14,16));
			
				var actual = data[i]['actual'];
				var forecast = data[i]['forecast'];
				
				// 실제 단위 통일
				if( actual.indexOf("M") !== -1 ) {
					actual = actual.replace(/[^0-9-.]/g,'');
					actual = ( actual * 100 );
				} else if( actual.indexOf("B") !== -1 ) {
					actual = actual.replace(/[^0-9-.]/g,'');
					//actual = ( actual * 1000000000 );
					//actual = ( actual / 1000 );
				} else if( actual.indexOf("T") !== -1 ) {
					actual = actual.replace(/[^0-9-.]/g,'');
					//actual = actual * 1000000000000;
					//actual = ( actual / 1000 );
				} else if( actual.indexOf("K") !== -1 ) {
					actual = actual.replace(/[^0-9-.]/g,'');
					actual = actual * 1000;
					//actual = ( actual / 1000 );
				}
				
				// 예상치 단위 통일
				if( forecast.indexOf("M") !== -1 ) {
					forecast = forecast.replace(/[^0-9-.]/g,'');
					forecast = ( forecast * 100 );

				} else if( forecast.indexOf("B") !== -1 ) {
					forecast = forecast.replace(/[^0-9-.]/g,'');
					//forecast = ( forecast * 1000000000 );
					//forecast = ( forecast / 1000 );
				} else if( forecast.indexOf("T") !== -1 ) {
					forecast = forecast.replace(/[^0-9-.]/g,'');
					//forecast = forecast * 1000000000000;
					//forecast = ( forecast / 1000 );
				} else if( forecast.indexOf("K") !== -1 ) {
					forecast = forecast.replace(/[^0-9-.]/g,'');
					forecast = forecast * 1000;
				}

				if( forecast == null || typeof forecast == "undefined" || forecast == "" )
					forecast = 0;
				/*
				// 단위에 따른 데이터 적용 작업
				if( unit.indexOf("M") !== -1 ) {
					actual = ( actual * 100 );
					forecast = ( forecast * 100 );
				} else if( unit.indexOf("B") !== -1 ) {
					actual = ( actual * 1000000000 );
					forecast = ( forecast * 1000000000 );
				} else if( unit.indexOf("T") !== -1 ) {
					actual = ( actual * 1000000000000 );
					forecast = ( forecast * 1000000000000 );
				} else if( unit.indexOf("K") !== -1 ) { 
					actual = ( actual * 1000 );
					forecast = ( forecast * 1000 );
				}
				*/

				// - 2.6%인 경우가 존재하므로 - 2.6% => -2.6%으로 수정하기 위함
				actual = String(actual).replace(" ","");
				forecast = String(forecast).replace(" ","");

				if( actual != "" ) {
					arr_actual.push([
						Date.UTC( dt_y, dt_m, dt_d, dt_h, dt_i ),
						parseFloat( actual )
					]);
				}
				
				// 예상치 존재유무
				if( state ) {
					if( forecast != "" ) {
						arr_forecast.push([
							Date.UTC( dt_y, dt_m, dt_d, dt_h, dt_i ),
							parseFloat( forecast )
						]);
					}
				}

			}

			// 헤럴드 차트 색상 추가 2020-11-15
			var custom_chart_color;
			var line_color = "black";
			/*
			if( cookie_cc == "hrd" ) {
				custom_chart_color = "#FDF0E7";
			} else if( cookie_cc == "sh" ){
				custom_chart_color = "#3c3c48";
				line_color = "#dac272";
			} else {
			*/
				custom_chart_color = "#FFF";	
			//}

			chart2 = new Highcharts.stockChart({
				
				navigation: {
					buttonOptions: {
						enabled: false // 우측 상단의 메뉴버튼 유무
					}
				},
				chart : {
					renderTo: div_id, // 차트를 어느 영역(div)에 그릴 것인가?
					animation: true,
					spacingTop: 20,
					spacingBottom: 5,
					style : {
						overflow : "visible"
					},
					backgroundColor: custom_chart_color
				},
				title: {
					text: '' // 차트 상단 제목 (차트영역을 많이 차지해서 사용안함)
				},
				credits:{
					enabled: false,
					text: 'wstock.edaily.co.kr',
					href: 'http://wstock.edaily.co.kr',
					position: {
						align: 'right',
						x: -5,
						verticalAlign: 'bottom',
						y: -5
					},
					style: {
						cursor: 'pointer',
						color: '#909090',
						fontSize: '9px'
					}					
				},
				plotOptions: {
					line: {
						animation: false
					},
					series: {
						animation: false,
						shadow: false,
						fillOpacity: 0.25,
						dataGrouping : {
							enabled : false
						}
					}
				},
				exporting: {
					enabled: false
				},			
				scrollbar: {
					enabled: false, // 하단 가로스크롤바
					height : 0
				},
				navigator: {
					enabled: false,
					height : 5,
					xAxis: {
						type: 'datetime',
						dateTimeLabelFormats: {
							day: '%Y/%m/%d',
							week: '%Y/%m',
							month: '%Y/%m',
							year: '%Y'
						}
					}
				},
				legend: {
					enabled: true,
					align : 'left',
					y : -19,
					x : -13,
					verticalAlign: 'top',
					floating : true,
					symbolWidth : 8,
					symbolHeight : 6,
					symbolPadding : 0,
					labelFormatter : function() {
						return '<span style="font-size:11px; color:'+this.color+'">' + this.name +'</span>';
					}
				},
				xAxis: {
					title: {
						text: ''
					},
					minRange: 1,
					type:'datetime',
					dateTimeLabelFormats: {
						minute: '%H:%M',
						hour: '%H:%M',
						day: '%m/%d',
						week: '%m/%d',
						month: '%Y/%m',
						year: '%Y'
					},
					lineWidth: 0,
					labels: {
						style:{
							fontSize: '12px' // 하단부 날짜 사이즈
						}
					}
				},
				yAxis: {
					title: {
						text: ''
					},
					opposite: true,
					lineWidth: 0,
					gridLineColor: "#bab9b9",
					labels: {
						style:{
							fontSize: '7px' // 우측부 숫자 사이즈
						}//,
						//formatter : function () {
						//	 return this.value;
						//}
					}
				},			
				tooltip: {
					crosshairs: {
						zIndex: 4
					},
					formatter: function () {
				
						var format = '%Y.%m.%d';					
						var s = '<b><span style="font-size:13px;">' + Highcharts.dateFormat(format, this.x) + '</span></b>'; // 연 월 일만

						$.each(this.points, function (i, point) {
							if( state ) {
								s += ( '<br/><span style="font-size:12px">'+this.series.name+' : </span><span style="font-weight:bold;font-size:12px;">' + number_format2( point.y, 2 )+ '</span>');
							} else {
								if( i == 0 ) {
									s += ( '<br/><span style="font-size:12px">'+this.series.name+' : </span><span style="font-weight:bold;font-size:12px;">' + number_format2( point.y, 2 )+ '</span>');
								}
							}

						});

						return s;
					},
					positioner: function (w, h, point) {
						return { x: point.plotX - w / 2, y: point.plotY - h };
					}
				},
				rangeSelector: {
					enabled: false,
					buttons: [{
						type: 'month',
						count: 3,
						text: '3m'
					}, {
						type: 'year',
						count: 1,
						text: '1y'
					}, {
						type: 'all',
						text: 'All'
					}, {
						type: 'day',
						count: 1,
						text: '1day'
					}],
					selected:2
				},
				series: [{
					type :"line",
					data : arr_actual,
					name : "실제",
					lineWidth: 1,
					states: {
						hover: {
							enabled: false,
							lineWidth: 1
						}
					}
				}, {
					data : arr_forecast,
					name : "예상",
					lineWidth: 1,
					visible : state,
					showInLegend : state,
					states: {
						hover: {
							enabled: false,
							lineWidth: 1
						}
					},
					color: line_color
				}]
			});
			
		});	
		
	}
```