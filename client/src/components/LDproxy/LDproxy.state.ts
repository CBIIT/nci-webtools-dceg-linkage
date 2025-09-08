import { PopOption } from "../select/pop-select";

export class LDproxyState {
  var: string = "";
  pop: PopOption[] = [{ value: "YRI", label: "(YRI) Yoruba in Ibadan, Nigera" }];
  r2_d: string = "r2";
  genome_build: string = "grch37";
  window: string = "500000";
  collapseTranscript: boolean = true;
  annotate: string = "forge";
  showAllSNPs: boolean = false;
  submitted: boolean = false;
}
