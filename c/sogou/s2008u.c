
//@brife        *Parse the log file from sogou seach engine*
//@dataset      *SogouQ 2012
//@author       *Xiangwen Wang*
//@data         *2014-05-20*
//@version      *1.3*
//@address      *Department of Physics, Virginia Tech*

#include<stdio.h>
#include<stdlib.h>
#include<math.h>
#include<string.h>
#include<time.h>

#define LEAST_D_NUM 0   //searches
#define MAX_L 128       //define max length of search content
#define MAX_JUMP 65535  //define max displacement
#define MAX_URL 65535   //define max number of results the search engine returns
#define GAP 100000      //this is used to show how many clickings have been examined
#define DIG_NUM 36      //how many different characters are allowed in the User_ID

typedef struct CCell{
	long url_d;
	long click_time;
	struct CCell *next_cc;
}CCell;

typedef struct Search{
	//one search, including the search content, search time, url order, last displacement
	char text[MAX_L];
	long url;
	long search_t;
	struct CCell *d_list;
	struct CCell *url_list;
	long d_num;  //number of displacements in this search
	struct Search *next;
	long incomplete;
	long lastorder;
}Search;

typedef struct User_str{
	//user, one user may submit several searches. A pointer is used to to link them
	char id[MAX_L];
	Search *p;
	struct User_str *next_id;
}User_str;

FILE *fp6=NULL,*fp7=NULL, *fp8=NULL, *fp9=NULL;


long listoutput(FILE *fp, CCell *p){
	if(p==NULL){
		fprintf(fp,"\n");
		return 0;
	}
	listoutput(fp,p->next_cc);
	if(p->click_time>=0) fprintf(fp,"%ld\t",p->click_time);
	fprintf(fp,"%ld\t",p->url_d);
	return 1;
}


long freelist(CCell *p){
	if(p==NULL) return 0;
	freelist(p->next_cc);
	free(p);
	return 1;
}


long ReleaseSearch(Search *p){
	if(!p) return 0;
	ReleaseSearch(p->next);
	fprintf(fp6,"%ld\n",p->lastorder);
	fprintf(fp7,"%ld\n",p->url);
	if(!(p->incomplete)){
		if(p->d_num>=LEAST_D_NUM){
			listoutput(fp8,p->d_list);
			listoutput(fp9,p->url_list);
		}
	}
	freelist(p->d_list);
	freelist(p->url_list);
	free(p);
	return 1;
}

long ReleaseUser(User_str *id){
	if(!id) return 0;
	ReleaseSearch(id->p);
	ReleaseUser(id->next_id);
	free(id);
	return 1;
}

long InitUser(User_str all[DIG_NUM][DIG_NUM][DIG_NUM][DIG_NUM]){
	long i=0,j=0,k=0,l=0;
	for(i=0;i<DIG_NUM;i++){
		for(j=0;j<DIG_NUM;j++){
			for(k=0;k<DIG_NUM;k++){
				for(l=0;l<DIG_NUM;l++){
					all[i][j][k][l].id[0]='\0';
					all[i][j][k][l].next_id=NULL;
					all[i][j][k][l].p=NULL;
				}
			}
		}
	}
	return 1;
}

long Destory(User_str all[DIG_NUM][DIG_NUM][DIG_NUM][DIG_NUM]){
	long i=0,j=0,k=0,l=0;
	for(i=0;i<DIG_NUM;i++){
		for(j=0;j<DIG_NUM;j++){
			for(k=0;k<DIG_NUM;k++){
				for(l=0;l<DIG_NUM;l++){
					ReleaseSearch(all[i][j][k][l].p);
					ReleaseUser(all[i][j][k][l].next_id);
					all[i][j][k][l].id[0]='\0';
					all[i][j][k][l].next_id=NULL;
					all[i][j][k][l].p=NULL;
				}
			}
		}
	}
	return 1;
}

long cal_index(char a){
	if((a>='0')&&(a<='9')) return a-'0';
	else return a+10-'a';
}

User_str* locate_p(User_str all[DIG_NUM][DIG_NUM][DIG_NUM][DIG_NUM], char cu_id[]){
	long i,j,k,l;
	i=cal_index(cu_id[0]);
	j=cal_index(cu_id[1]);
	k=cal_index(cu_id[2]);
	l=cal_index(cu_id[3]);
	return &all[i][j][k][l];
}

int main(int argc, char* argv[]){
	if(argc==1) exit(0);
	char ch=10;
	long user_num=0, cu_t=0, cu_order=0;  //number of user, search time in number
	long percent=1;
	long id_i=0, search_i=0, cu_rank=0, new_id=1, new_sear=1;
	char cu_id[32],cu_sear[MAX_L];	//user id, search contant, search time

	Search *p_next=NULL, *p_curr=NULL, *p_temp=NULL;
	
	CCell *temp_cc;

	static User_str all[DIG_NUM][DIG_NUM][DIG_NUM][DIG_NUM];
	User_str* temp_p=NULL;

	FILE *fp1=NULL,*fp2=NULL,*fp3=NULL, *fp4=NULL, *fp5=NULL;
	FILE *fp3=NULL,*fp4=NULL,*fp5=NULL,*fp6=NULL,*fp7=NULL;

//	fp1=fopen("sogou.filter","r");		//fp1 is the origin search data file
	char orifile[32]="log";
	char resfiled[32]="raw_n_r",resfilet[32]="raw_n_t",resfile_corr[32]="raw_t_r";
	char resfile_s_t[32]="raw_search_t", resfile_c_n[32]="raw_click_num", resource_file[32]="resource_";
	char d_list_file[32]="d_list", url_list_file[32]="url_list";
	strcat(orifile,argv[1]);
	strcat(orifile,".dat");
	strcat(resfiled,argv[1]);
	strcat(resfiled,".dat");
	strcat(resfilet,argv[1]);
	strcat(resfilet,".dat");
	strcat(resfile_corr,argv[1]);
	strcat(resfile_corr,".dat");
	strcat(resfile_s_t,argv[1]);
	strcat(resfile_s_t,".dat");
	strcat(resfile_c_n,argv[1]);
	strcat(resfile_c_n,".dat");
	strcat(resource_file,argv[1]);
	strcat(resource_file,".dat");
	strcat(d_list_file,argv[1]);
	strcat(d_list_file,".dat");
	strcat(url_list_file,argv[1]);
	strcat(url_list_file,".dat");
	fp1=fopen(orifile,"r");
	fp2=fopen(resfiled,"a");		//fp2 is the displacements data file
	fp3=fopen(resfilet,"a");		//fp3 is the interval time data file
	fp4=fopen(resfile_corr,"a");	//fp4 will be used to calculate the correlation
	fp5=fopen(resfile_s_t,"a");		//fp5
	fp6=fopen(resfile_c_n,"a");		//fp6
	fp7=fopen(resource_file,"a");	//fp7 sotres the resource locations
	fp8=fopen(d_list_file,"a");		//fp8 stores the d series
	fp9=fopen(url_list_file,"a");	//fp9 stores the (t,r) series
	//---------------------------------------------------
	InitUser(all);
	
	while(1){   //  D
		if(!(percent++%GAP)) printf("%ld Finished\n", percent-1); //to show how many search processed

		fscanf(fp1,"%ld\t",&cu_t);
		if(feof(fp1)) goto END;
		while((ch=fgetc(fp1))!=9) {	//get the users' id in string
			cu_id[id_i++]=ch;
		}
		cu_id[id_i]='\0';
		id_i=0;

		while((ch=fgetc(fp1))!=9) {	//get the search content
			cu_sear[search_i++]=ch;
		}
		cu_sear[search_i]='\0';
		search_i=0;

		fscanf(fp1,"%ld\t%ld\n",&cu_rank,&cu_order);	//get the order of url

		//printf("%ld\n",cu_rank);
		//-----------------------Data processing----------------------
		if(cu_rank<MAX_URL){ //make sure the clicking is legal	 C
			new_id=1;	
			new_sear=1;
			temp_p=locate_p(all,cu_id);
			while(temp_p->next_id){
				if(!strcmp(temp_p->next_id->id,cu_id)) {
					temp_p=temp_p->next_id;
					new_id=0;
					break;
				}
				temp_p=temp_p->next_id;
			}
			if(!strcmp(temp_p->id,cu_id)) new_id=0;
			if(new_id){	//if it is a new user, than add it to the user array
				temp_p->next_id=(User_str *)malloc(sizeof(User_str));
				temp_p=temp_p->next_id;
				strcpy(temp_p->id, cu_id);
				temp_p->next_id=NULL;
				temp_p->p=(Search *)malloc(sizeof(Search)); //add new search
				strcpy(temp_p->p->text, cu_sear);
				temp_p->p->url=cu_rank;
				temp_p->p->search_t=cu_t;
				temp_p->p->d_num=0;
				temp_p->p->d_list=NULL;
				temp_p->p->url_list=(CCell *)malloc(sizeof(CCell));
				temp_p->p->url_list->url_d=cu_rank;
				temp_p->p->url_list->click_time=cu_t;
				temp_p->p->url_list->next_cc=NULL;
				if(cu_order==1) temp_p->p->incomplete=0;
				else temp_p->p->incomplete=1;
				temp_p->p->lastorder=cu_order;
				temp_p->p->next=NULL;
				user_num+=1;
			}
			
			else{	 //if it is a existed user, find the user   B
				p_next=temp_p->p;
				do{ //check if it is a new search
					if(!strcmp(p_next->text,cu_sear)){ 
						new_sear=0; //if it is a existed search, find it in the search array
						break;
					}
					p_curr=p_next;
					p_next=p_next->next;
				}while(p_next!=NULL);

				if(new_sear){ 	//if it is a new search, than add it to the search array				
					p_curr->next=(Search *)malloc(sizeof(Search));
					p_temp=p_curr->next;
					strcpy(p_temp->text, cu_sear);
					p_temp->url=cu_rank;
					p_temp->search_t=cu_t;
					if(cu_order==1) p_temp->incomplete=0;
					else p_temp->incomplete=1;
					p_temp->lastorder=cu_order;
					p_temp->next=NULL;
					p_temp->d_num=0;
					p_temp->d_list=NULL;
					p_temp->url_list=(CCell *)malloc(sizeof(CCell));
					p_temp->url_list->url_d=cu_rank;
					p_temp->url_list->click_time=cu_t;
					p_temp->url_list->next_cc=NULL;
					fprintf(fp5,"%ld\n",cu_t-p_curr->search_t);	
				}

				else{ // A
					//if it is a existed search
					//calculate the time interval, displacements, etc.
					//and output
					if(cu_order>p_next->lastorder){
						fprintf(fp2,"%ld\t%ld\n",cu_order,cu_rank);
						if(!(p_next->incomplete)){
							fprintf(fp3,"%ld\t%ld\n",cu_order,cu_t-p_next->search_t);
							fprintf(fp4,"%ld\t%ld\n",cu_t-p_next->search_t,cu_rank);
						}
						p_next->d_num+=1;
						temp_cc=(CCell *)malloc(sizeof(CCell)); //url_list
						temp_cc->url_d=cu_rank;
						temp_cc->click_time=cu_t;
						temp_cc->next_cc=p_next->url_list;
						p_next->url_list=temp_cc;
						temp_cc=(CCell *)malloc(sizeof(CCell)); //d_list
						temp_cc->url_d=cu_rank-p_next->url;
						temp_cc->click_time=-1;
						temp_cc->next_cc=p_next->d_list;
						p_next->d_list=temp_cc;
					}
					else{
						p_next->search_t=cu_t;
						fprintf(fp6,"%ld\n",p_next->lastorder);
						fprintf(fp7,"%ld\n",p_next->url);
						if(!(p_next->incomplete)){
							if(p_next->d_num>=LEAST_D_NUM){
								listoutput(fp8,p_next->d_list);
								listoutput(fp9,p_next->url_list);
							}
						}
						freelist(p_next->d_list);
						freelist(p_next->url_list->next_cc);
						if(cu_order==1) p_next->incomplete=0;
						else p_next->incomplete=1;
						p_next->d_num=0;
						p_next->d_list=NULL;
						p_next->url_list->next_cc=NULL;
						p_next->url_list->url_d=cu_rank;
					}
					//p_next->lastjump=cu_rank-p_next->url;  
					p_next->url=cu_rank;
					p_next->lastorder=cu_order;
					
				}   // end of A
			}	//end of B
		}  //end of C
	} // end of D
	//----------------------------------------------------------------------	
	END:
	fclose(fp1);
	fclose(fp2);
	fclose(fp3);
	fclose(fp4);
	fclose(fp5);

	Destory(all);
	fclose(fp6);
	fclose(fp7);
	printf("%s Finished.\n\n",argv[1]);
	return 1;
}
