#include <stdio.h>
#include <string.h>


int main(int argc, char *argv[]){
    FILE *arq;
    if(argc<2) return 1;
    int linha=1, coluna=0, c, token =0;
    
    arq = fopen(argv[1], "r");
    if(arq == NULL) return 1;

    while((c = fgetc(arq)) != EOF){
        coluna++;
        if(c ==' ' || c == '\n'){
            token++;
            printf("Token achado.\nNa linha %d e na coluna %d.\n\n", linha, coluna);
             if(c == '\n'){
                linha++;
                coluna=0;
                continue;
            }
        } 
    }
    if(coluna>0) token++;
    printf("Quantidade de tokens: %d e numero da ultima coluna %d\n", token, coluna);
    fclose(arq);
    return 0;
}

