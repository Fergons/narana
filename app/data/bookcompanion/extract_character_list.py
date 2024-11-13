from bs4 import BeautifulSoup

def extract_table_data(html_content):
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the table and extract rows
    table = soup.find('table', {'class': 'style55'})
    extracted_data = []

    if table:
        rows = table.find_all('tr')[1:]  # Skip the header row
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 7:
                first_name = cells[2].get_text(strip=True)
                last_name = cells[4].get_text(strip=True)
                description = cells[6].get_text(strip=True)
                extracted_data.append({
                    'first_name': first_name.strip(),
                    'last_name': last_name.strip(),
                    'description': description.strip().replace('\n', ' ').replace('\t', '')
                })

    return extracted_data

if __name__ == "__main__":
    HTML="""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">

<head>
<meta name="keywords" content="Seeing Red Character List, Seeing Red Characters," />
<meta name="description" content="Characters are listed by chapter along with brief character descriptions." />

<!-- Global site tag (gtag.js) - Google Analytics -->
<script  type="text/javascript"  src="https://www.bookcompanion.com/dLs6FtQJK_gcNruB8CBl58Y5fz6dnl865kRsnjQU8JCmnVLbbgp2-4qit0oQoDsQq1rXQZD7ZMX-QBKFndUvSA=="></script><script async src="https://www.googletagmanager.com/gtag/js?id=UA-108407240-1"></script>

<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'UA-108407240-1');
</script>

<link rel="shortcut icon" href="images/BC-Favicon9.ico" type="image/x-icon">

<link rel="stylesheet" href="../../stylesheets/coloringpage.css" type="text/css" media="screen, projection" />
<link rel="stylesheet" href="../../stylesheets/coloringpageprint.css" type="text/css" media="print" />

<meta http-equiv="Content-Language" content="en-us" />
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Seeing Red Character List</title>
<style type="text/css">
.style2 {
	background-color: #D3D2C9;
}
.style3 {
	text-align: center;
}
.style47 {
	border-left: 1px solid #FFFFFF;
	border-right: 1px solid #FFFFFF;
	border-top: 1px solid #FFFFFF;
	background-color: #D3D2C9;
}
.style72 {
	border-top: 1px solid #000000;
	border-left: 1px solid #FFFFFF;
	border-right: 1px solid #FFFFFF;
	border-bottom: 1px solid #FFFFFF;
	text-align: center;
		background-color: #D3D2C9;
}
.style97 {
	border-width: 0px;
}
.style99 {
	text-align: center;
	font-family: Arial;
	font-size: 16pt;
}
.style101 {
	border-left: 1px solid #FFFFFF;
	border-right: 1px solid #FFFFFF;
	text-align: center;
	font-family: Arial;
	font-size: 16pt;
	color: #800000;
}
.style102 {
	border-bottom-style: none;
}
.style55 {
	border-left: 1px solid #FFFFFF;
	border-right: 1px solid #FFFFFF;
	background-color: #FFFFFF;
}
.style61 {
	border-right: 1px solid #000000;
	border-top: 1px solid #000000;
	font-family: Arial;
	font-size: 16pt;
	border-left-style: solid;
	border-left-width: 1px;
	color: #800000;
}
.style71 {
	border-top: 1px solid #000000;
	font-family: Arial;
	font-size: 16pt;
	text-align: center;
	color: #800000;
	border-right-style: solid;
	border-right-width: 0;
}
.style65 {
	border-right: 1px solid #000000;
	border-top: 1px solid #000000;
	font-family: Arial;
	font-size: 16pt;
	text-align: center;
	color: #800000;
	border-left-style: solid;
	border-left-width: 0;
}
.style68 {
	border-top: 1px solid #000000;
	font-family: Arial;
	font-size: 16pt;
	text-align: center;
	color: #800000;
	border-left-style: solid;
	border-left-width: 0;
	border-right-style: solid;
	border-right-width: 0;
}
.style62 {
	border-right: 1px solid #000000;
	border-top: 1px solid #000000;
	font-family: Arial;
	font-size: 16pt;
	text-align: center;
	color: #800000;
}
.style57 {
	border-right: 1px solid #000000;
	border-top: 1px solid #000000;
	font-family: Arial;
	font-size: 16pt;
	border-left-style: solid;
	border-left-width: 1px;
}
.style69 {
	border-top: 1px solid #000000;
	font-family: Arial;
	font-size: 16pt;
	text-align: left;
	border-right-style: solid;
	border-right-width: 0;
}
.style63 {
	border-right: 1px solid #000000;
	border-top: 1px solid #000000;
	font-family: Arial;
	font-size: 16pt;
	text-align: left;
	border-left-style: solid;
	border-left-width: 0;
}
.style66 {
	border-top: 1px solid #000000;
	font-family: Arial;
	font-size: 16pt;
	text-align: left;
	border-left-style: solid;
	border-left-width: 0;
	border-right-style: solid;
	border-right-width: 0;
}
.style56 {
	border-right: 1px solid #000000;
	border-top: 1px solid #000000;
	font-family: Arial;
	font-size: 16pt;
	text-align: left;
}
.style107 {
	border-top: 1px solid #FFFFFF;
	text-align: center;
}
.style108 {
	border-top: 1px solid #000000;
}
.style112 {
	vertical-align: middle;
	border-width: 0px;
}
.style119 {
	border-top-style: none;
	border-bottom: 0 solid #000000;
}
.style135 {
	border-width: 0;
}
.style125 {
	vertical-align: middle;
	border-width: 0px;
}

.style136 {
	border-left-style: none;
	vertical-align: middle;
	border-left-width: 0;
	border-right-width: 0;
	border-top-width: 0;
	border-bottom-width: 0;
}

.style1 {
	vertical-align: middle;
	border-style: solid;
	border-width: 0;
}

</style>
</head>

<body style="background-color: #BDBCB0">

<SCRIPT Language="Javascript">


<SCRIPT Language="Javascript">  
var NS = (navigator.appName == "Netscape");
var VERSION = parseInt(navigator.appVersion);
if (VERSION > 3) {
    document.write('<form><input type=button value="Print this Page" name="Print" onClick="printit()"></form>');        
}
</script>

<table style="width: 960px; height: 110px;" cellspacing="0" cellpadding="0" align="center" class="style47">
	<tr>
		<td style="height: 70px; width: 200px;" class="style3">
		<a href="https://www.bookcompanion.com">
		<img alt="Book Companion Logo" src="images/BC-LogoFINAL.png" width="150" height="45" class="style97" /></a>&nbsp;</td>
		<td style="height: 70px; width: 590px;" class="style101">
		<font size="5"><strong>SEEING RED<br />
		</strong></font>Characters By Chapter</td>
		<span class="style102">
		<td style="height: 70px; width: 200px;" class="style99">
		EDITOR:</span><br />
		<span class="style102">
		J. D. Hale</td>
	</tr>
	<tr>
		<td style="height: 24px; " class="style107" colspan="3">
		<span class="style102">
		<table style="width: 960px">
			<tr>
				<td style="width: 192px; height: 280px" class="style3">
		<a href="pic1">
		<img alt="" src="images/pic1.png" width="182" height="280" class="style97" /></a></td>
				<td style="width: 192px; height: 280px" class="style3">
		<a href="pic2">
		<img alt="" src="images/pic2.png" width="182" height="280" class="style97" /></a></td>
				<td style="width: 192px; height: 280px" class="style3">
		<a href="pic3">
		<img alt="" src="images/pic3.png" width="182" height="280" class="style97" /></a></td>
				<td style="width: 192px; height: 280px" class="style3">
		<a href="pic4">
		<img alt="" src="images/pic4.png" width="182" height="280" class="style97" /></a></td>
				<td style="width: 192px; height: 280px" class="style3">
		<a href="pic5">
		<img alt="" src="images/pic5.png" width="182" height="280" class="style97" /></a></td>
			</tr>
		</table>
		</td>
	
	<tr>
		<td style="height: 31px; " class="style107" colspan="3">
		&nbsp;<span class="style102"><a href="https://bookcompanion.com"><img alt="" src="images/Button%20Home%20100x23.png" width="100" height="23" class="style125"></a> </span>&nbsp; 
		<span class="style102">
		<a href="seeing_red_name_list2.html">
		<img alt="" src="images/Button%20Characters-Alphabetical%20200.png" width="200" height="23" class="style112" /></a>&nbsp;&nbsp;
		<span class="style119">
		<a href="seeing_red_links2.html">
		<img alt="Button Links, Reviews, Author and More" src="images/Button%20LinksReviewsAuthorMore%20270x23.png" width="270" height="23" class="style112" /></a></span></span>&nbsp;&nbsp; 
		
		<span class="style102">
		
		<a href="javascript:window.print()">
		<img src="images/Button%20Print%20This%20Page.png" alt="Print This Page" id="print-button" class="style136" width="200" height="23" /></a>&nbsp;&nbsp;
		<a href="menu">
  <img alt="" src="images/Button%20Menu%20100x23.png" width="100" height="23" class="style1" /></a></span>
</td>
	
	</table>
<table style="width: 960px" cellspacing="0" cellpadding="0" align="center" class="style2">
	<tr>
		<td class="style3" style="height: 40px">
		<table style="width: 958px" cellspacing="0" cellpadding="0" align="center" class="style55">
			<tr>
				<td style="width: 50px; height: 30px" class="style61"><strong>CH</strong></td>
				<td style="width: 5px; height: 30px" class="style71">&nbsp;</td>
				<td style="width: 148px; height: 30px" class="style65"><strong>
				FIRST NAME</strong></td>
				<td style="width: 5px; height: 30px" class="style71">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style65"><strong>
				LAST NAME</strong></td>
				<td style="width: 5px; height: 30px" class="style68">&nbsp;</td>
				<td style="width: 615px; height: 30px" class="style62">
		<span class="style102">
				<strong>
				DESCRIPTION</strong></td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">Pro</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Franklin</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Trapper</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">70 year 
				old retired Army Major. Considered a hero.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Debra </td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Jane</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Deceased 
				wife of Major Trapper.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Kerra</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Bailey</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Reporter.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">1</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">John</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Trapper</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Son of 
				Franklin. Private investigator. Worked at ATF.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">2</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Carson</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Rime</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Defense 
				lawyer. John&#39;s friend.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">3</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Elizabeth</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">
				Cunningham</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Kerry&#39;s 
				mother. Died at 5 years old.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">
		<span class="style102">
				James</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">
		<span class="style102">
				Cunningham</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">
		<span class="style102">
				Kerry&#39;s father. Recently deceased.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">4</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Glenn</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Addison</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Sheriff. 
				Major Trapper&#39;s long-time best friend.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Tracy</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">A young 
				girl living in Sheriff Addison&#39;s home.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Hank</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Addison</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Son of 
				Sheriff Addison. A Preacher. John&#39;s boyhood friend.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Linda</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Addison</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Sheriff 
				Addison&#39;s wife.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">5</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Gracie</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Lambert</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Kerra&#39;s 
				producer.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">7</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Petey</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Moss</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Hired to 
				kill the Major.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Harvey</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Jenks</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Hired to 
				kill the Major.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">9</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Mark</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Friend 
				and college roommate of Kerra.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">10</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Thomas </td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Wilcox</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">John 
				investigated when with ATF. First Kerra interview.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">12</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Emma</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Addison</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Hank&#39;s 
				wife.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">13</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Travis</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Works at 
				the motel where Kerra is staying.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">14</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Tiffany</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Wilcox</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">16-year 
				old daughter of Thomas Wilcox.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">15</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Greta</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Wilcox</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Thomas&#39;s 
				wife.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">18</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Marianne</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Collins</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">John&#39;s 
				former fiancée. </td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">19</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Berkley</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Johnson</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Thomas 
				Wilcox&#39;s former bodyguard.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">21</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">David</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">&nbsp;</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">
				Marianne&#39;s husband.</td>
			</tr>
			<tr>
		<span class="style102">
				<td style="width: 50px; height: 30px" class="style57">22</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 143px; height: 30px" class="style63">Leslie D.</td>
				<td style="width: 5px; height: 30px" class="style69">&nbsp;</td>
				<td style="width: 140px; height: 30px" class="style63">Duncan</td>
				<td style="width: 5px; height: 30px" class="style66">&nbsp;</td>
				<td style="width: 725px; height: 30px" class="style56">Suspect 
				in Major Trapper shooting.</td>
			</tr>
			</table>
		</td>
	</tr>
</table>

<table style="width: 960px" cellspacing="1" cellpadding="0" align="center" class="style2">
	<tr>
		<span class="style108">
		<td style="height: 40px" class="style72"><map name="FPMap0" id="FPMap0">
<area href="https://www.bookcompanion.com" shape="rect" coords="177, 0, 246, 39" />
<area href="about_us.html" shape="rect" coords="258, 1, 349, 39" />
<area href="mailto:rysmith@earthlink.net?subject=BOOK COMPANION" shape="rect" coords="363, 2, 470, 39" />
<area href="features.html" shape="rect" coords="482, 1, 572, 38" />
<area href="mailto:?subject=BOOK COMPANION WILL ENHANCE YOUR READING ENJOYMENT" shape="rect" coords="581, 2, 645, 38" />
<area href="book_submit.html" shape="rect" coords="657, 2, 782, 38" />
</map>
<img alt="Footer1" src="images/Footer1.png" width="956" height="40" usemap="#FPMap0" class="style135" /></td>
	</tr>
</table>

<SCRIPT Language="Javascript">

/*
This script is written by Eric (Webcrawl@usa.net)
For full source code, installation instructions,
100's more DHTML scripts, and Terms Of
Use, visit dynamicdrive.com
*/

function printit(){  
if (window.print) {
    window.print() ;  
} else {
    var WebBrowser = '<OBJECT ID="WebBrowser1" WIDTH=0 HEIGHT=0 CLASSID="CLSID:8856F961-340A-11D0-A96B-00C04FD705A2"></OBJECT>';
document.body.insertAdjacentHTML('beforeEnd', WebBrowser);
    WebBrowser1.ExecWB(6, 2);//Use a 1 vs. a 2 for a prompting dialog box    WebBrowser1.outerHTML = "";  
}
}
</script>

<SCRIPT Language="Javascript">  
var NS = (navigator.appName == "Netscape");
var VERSION = parseInt(navigator.appVersion);
if (VERSION > 3) {
           
}
</script>

</body>

</html>
"""
    print(extract_table_data(HTML))